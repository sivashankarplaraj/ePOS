from django.test import TestCase
from django.urls import reverse
from update_till.models import PdItem, PdVatTb, AppProd, CompPro, OptPro
from manage_orders.models import Order, OrderLine
from manage_orders.services.daily_stats import build_daily_stats
from django.utils import timezone
from datetime import timedelta


def _mk_product(code, name, std, meal=None, dc=None, vat_class=1):
    return PdItem.objects.create(
        PRODNUMB=code,
        PRODNAME=name,
        EAT_VAT_CLASS=vat_class,
        TAKE_VAT_CLASS=vat_class,
        READBACK_ORD=1,
        MEAL_ONLY=False,
        MEAL_CODE=0,
        MEAL_DRINK=meal or 0,
        T_DRINK_CD=0,
        VATPR=std,
        DC_VATPR=dc if dc is not None else 0,
        VATPR_2=std,
        DC_VATPR_2=dc if dc is not None else 0,
        VATPR_3=std,
        DC_VATPR_3=dc if dc is not None else 0,
        VATPR_4=std,
        DC_VATPR_4=dc if dc is not None else 0,
        VATPR_5=std,
        DC_VATPR_5=dc if dc is not None else 0,
        VATPR_6=std,
        DC_VATPR_6=dc if dc is not None else 0,
    )


class ManageOrdersBasicTests(TestCase):
    def setUp(self):
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')

    def test_index_redirects_to_order(self):
        resp = self.client.get(reverse('manage_orders_index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Create Order', resp.content)

    def test_order_url(self):
        resp = self.client.get(reverse('manage_orders_order'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Price Band', resp.content)

    def test_submit_simple_product_order(self):
        _mk_product(3, 'Cheeseburger', 485, dc=485)
        payload = {
            'price_band': '1',
            'vat_basis': 'take',
            'show_net': False,
            'lines': [
                {
                    'code': 3,
                    'type': 'product',
                    'name': 'Cheeseburger',
                    'variant': None,
                    'meal': False,
                    'qty': 1,
                    'price_gross': 485,
                    'meta': {},
                }
            ],
        }
        resp = self.client.post(
            reverse('mo_api_submit_order'),
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['total_gross'], 485)

    def test_meal_price_recomputed(self):
        _mk_product(3, 'Cheeseburger', 485, dc=485)
        _mk_product(30, 'Regular Fries', 205, dc=125)
        _mk_product(69, 'Vanilla Shake', 270, dc=260, meal=1)
        AppProd.objects.create(
            PRODNUMB=3,
            PRODNAME='Cheeseburger',
            GROUP_ID=1,
            GROUP_SUB_ID=1,
            MEAL_ID=1,
            MEAL_SUB_ID=1,
            DOUBLE_PDNUMB=0,
            TRIPLE_PDNUMB=0,
        )
        wrong_client_price = 485  # deliberately wrong
        payload = {
            'price_band': '1',
            'vat_basis': 'take',
            'show_net': False,
            'lines': [
                {
                    'code': 3,
                    'type': 'product',
                    'name': 'Cheeseburger Meal',
                    'variant': None,
                    'meal': True,
                    'qty': 1,
                    'price_gross': wrong_client_price,
                    'meta': {'fries': 30, 'drink': 69, 'options': []},
                }
            ],
        }
        resp = self.client.post(
            reverse('mo_api_submit_order'),
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['total_gross'], 485 + 125 + 260)


class StatsAggregationTests(TestCase):
    def setUp(self):
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')

    def _prod(self, code, name, price, dc=None):
        return PdItem.objects.create(
            PRODNUMB=code, PRODNAME=name, EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
            READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
            VATPR=price, DC_VATPR=dc or 0,
            VATPR_2=price, DC_VATPR_2=dc or 0,
            VATPR_3=price, DC_VATPR_3=dc or 0,
            VATPR_4=price, DC_VATPR_4=dc or 0,
            VATPR_5=price, DC_VATPR_5=dc or 0,
            VATPR_6=price, DC_VATPR_6=dc or 0,
        )

    def test_combination_discount_and_option_and_staff_waste(self):
        # Components and optional dips
        self._prod(71,'Six Bites',530)
        self._prod(82,'Onion Rings 8',245)
        self._prod(95,'Mozarela Fingers',315)
        self._prod(26,'Dip Ketchup',55)
        self._prod(39,'Dip BBQ',75)
        # Combo product (price less than sum components + dips)
        self._prod(4,'Sharing Platter',995)
        # Relationships
        CompPro.objects.create(COMBONUMB=4, PRODNUMB=71, T_PRODNUMB=0)
        CompPro.objects.create(COMBONUMB=4, PRODNUMB=82, T_PRODNUMB=0)
        CompPro.objects.create(COMBONUMB=4, PRODNUMB=95, T_PRODNUMB=0)
        OptPro.objects.create(COMBONUMB=4, PRODNUMB=26, T_PRODNUMB=0)
        OptPro.objects.create(COMBONUMB=4, PRODNUMB=39, T_PRODNUMB=0)
        # Create order with one combo line selecting two optional dips; payment method crew food (STAFF)
        order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Crew Food')
        OrderLine.objects.create(order=order, item_code=4, item_type='combo', name='Sharing Platter', variant_label='', is_meal=False, qty=1, unit_price_gross=995, line_total_gross=995, meta={'options':[26,39]})
        # Waste order single product
        waste_order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Waste food')
        OrderLine.objects.create(order=waste_order, item_code=71, item_type='product', name='Six Bites', variant_label='', is_meal=False, qty=1, unit_price_gross=530, line_total_gross=530, meta={})
        build_daily_stats(timezone.localdate())
        # Validate KRev combination discount: (530+245+315+55+75) - 995 = 225
        from update_till.models import KRev, KPro
        rev = KRev.objects.get(stat_date=timezone.localdate())
        self.assertEqual(rev.TDISCNTVA, 225)
        # STAFF count for combo product
        combo_row = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=4, COMBO=True)
        self.assertEqual(combo_row.STAFF, 1)
        # Staff combo should not increment TAKEAWAY/EATIN basis counts
        self.assertEqual(combo_row.TAKEAWAY, 0)
        self.assertEqual(combo_row.EATIN, 0)
        # WASTE count for product 71
        prod_row = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=71, COMBO=False)
        self.assertEqual(prod_row.WASTE, 1)
        # Waste product should not increment TAKEAWAY/EATIN basis counts
        self.assertEqual(prod_row.TAKEAWAY, 0)
        self.assertEqual(prod_row.EATIN, 0)
        # OPTION count for dips (26 and 39) inside combo should be 0 (combo free items do not count in OPTION)
        dip26 = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=26, COMBO=False)
        dip39 = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=39, COMBO=False)
        self.assertEqual(dip26.OPTION, 0)
        self.assertEqual(dip39.OPTION, 0)

    def test_staff_and_waste_single_product_counts(self):
        # Product and VAT setup
        self._prod(200,'Sample Prod',500)
        day = timezone.localdate() + timedelta(days=4)
        staff_order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Crew Food', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=staff_order, item_code=200, item_type='product', name='Sample Prod', variant_label='', is_meal=False, qty=2, unit_price_gross=500, line_total_gross=1000, meta={})
        waste_order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Waste food', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=waste_order, item_code=200, item_type='product', name='Sample Prod', variant_label='', is_meal=False, qty=3, unit_price_gross=500, line_total_gross=1500, meta={})
        build_daily_stats(day)
        from update_till.models import KPro
        row = KPro.objects.get(stat_date=day, PRODNUMB=200, COMBO=False)
        self.assertEqual(row.STAFF, 2, 'Staff quantity should accumulate in STAFF only')
        self.assertEqual(row.WASTE, 3, 'Waste quantity should accumulate in WASTE only')
        self.assertEqual(row.TAKEAWAY, 0, 'TAKEAWAY basis should not increment for staff/waste orders')
        self.assertEqual(row.EATIN, 0, 'EATIN basis should not increment for staff/waste orders')

    def test_go_large_and_meal_discount(self):
        # Burger + fries + drink with discounted meal prices
        self._prod(3,'Cheeseburger',505, dc=505)
        self._prod(30,'Regular Fries',220, dc=130)
        self._prod(31,'Large Fries',250, dc=170)
        self._prod(69,'Vanilla Shake',285, dc=280)
        # Meal order take away, go large true (meta.go_large)
        order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Cash')
        # Effective meal price uses discounted components: 505 + 170 + 280 = 955; singles total 505+250+285=1040 discount=85
        OrderLine.objects.create(order=order, item_code=3, item_type='product', name='Cheeseburger Meal', variant_label='', is_meal=True, qty=1, unit_price_gross=955, line_total_gross=955, meta={'fries':31, 'drink':69, 'go_large': True})
        build_daily_stats(timezone.localdate())
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=timezone.localdate())
        self.assertEqual(rev.TMEAL_DISCNT, 85)
        self.assertEqual(rev.TGOLARGENU, 1)

    def test_vat_and_act_mirroring(self):
        # Simple two orders with different payment methods to populate TCASHVAL, TCARDVAL and VAT
        PdVatTb.objects.all().delete()
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')
        # Product with price 120 (implies VAT 20 if rate 20%)
        self._prod(500,'Std Prod',120)
        cash_order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Cash', total_gross=120)
        OrderLine.objects.create(order=cash_order, item_code=500, item_type='product', name='Std Prod', variant_label='', is_meal=False, qty=1, unit_price_gross=120, line_total_gross=120, meta={})
        card_order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Card', total_gross=240)
        OrderLine.objects.create(order=card_order, item_code=500, item_type='product', name='Std Prod', variant_label='', is_meal=False, qty=2, unit_price_gross=120, line_total_gross=240, meta={})
        build_daily_stats(timezone.localdate())
        from update_till.models import KRev, KWkVat
        rev = KRev.objects.get(stat_date=timezone.localdate())
        # Payment mirroring
        self.assertEqual(rev.TCASHVAL, 120)
        self.assertEqual(rev.TCARDVAL, 240)
        self.assertEqual(rev.ACTCASH, rev.TCASHVAL)
        self.assertEqual(rev.ACTCARD, rev.TCARDVAL)
        # VAT: total gross 360, at 20% VAT implies VAT portion = gross - gross/1.2 = 60 (integer rounding tolerated)
        self.assertTrue( FiftyNineSixty := (rev.VAT in {59,60}))
        # KWkVat row should reflect VAT for today's weekday column
        kv = KWkVat.objects.get(VAT_CLASS=1)
        weekday = timezone.localdate().isoweekday()  # 1..7
        vat_col = f'TOT_VAT_{weekday}'
        self.assertTrue(getattr(kv, vat_col) > 0)

    def test_vat_basis_takeaway_uses_take_vat_class_zero_rate(self):
        # Setup VAT classes: 0% for class 0, 20% for class 1
        PdVatTb.objects.all().delete()
        PdVatTb.objects.create(VAT_CLASS=0, VAT_RATE=0.0, VAT_DESC='Zero')
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')
        # Product with TAKE=0 (no VAT) and EAT=1 (20% VAT)
        PdItem.objects.create(
            PRODNUMB=900,
            PRODNAME='Strawberry Shk',
            EAT_VAT_CLASS=1,
            TAKE_VAT_CLASS=0,
            READBACK_ORD=1,
            MEAL_ONLY=False,
            MEAL_CODE=0,
            MEAL_DRINK=0,
            T_DRINK_CD=0,
            VATPR=300, DC_VATPR=0,
            VATPR_2=300, DC_VATPR_2=0,
            VATPR_3=300, DC_VATPR_3=0,
            VATPR_4=300, DC_VATPR_4=0,
            VATPR_5=300, DC_VATPR_5=0,
            VATPR_6=300, DC_VATPR_6=0,
        )
        day = timezone.localdate()
        order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Cash', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=order, item_code=900, item_type='product', name='Strawberry Shk', variant_label='', is_meal=False, qty=1, unit_price_gross=300, line_total_gross=300, meta={})
        build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        self.assertEqual(rev.VAT, 0, 'Takeaway should use TAKE_VAT_CLASS=0 (zero rate) so VAT=0')

    def test_vat_basis_eatin_uses_eat_vat_class_twenty_percent(self):
        # Setup VAT classes: 0% for class 0, 20% for class 1
        PdVatTb.objects.all().delete()
        PdVatTb.objects.create(VAT_CLASS=0, VAT_RATE=0.0, VAT_DESC='Zero')
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')
        # Product with TAKE=0 (no VAT) and EAT=1 (20% VAT)
        PdItem.objects.update_or_create(
            PRODNUMB=900,
            defaults=dict(
                PRODNAME='Strawberry Shk',
                EAT_VAT_CLASS=1,
                TAKE_VAT_CLASS=0,
                READBACK_ORD=1,
                MEAL_ONLY=False,
                MEAL_CODE=0,
                MEAL_DRINK=0,
                T_DRINK_CD=0,
                VATPR=300, DC_VATPR=0,
                VATPR_2=300, DC_VATPR_2=0,
                VATPR_3=300, DC_VATPR_3=0,
                VATPR_4=300, DC_VATPR_4=0,
                VATPR_5=300, DC_VATPR_5=0,
                VATPR_6=300, DC_VATPR_6=0,
            )
        )
        day = timezone.localdate() + timedelta(days=1)
        order = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Cash', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=order, item_code=900, item_type='product', name='Strawberry Shk', variant_label='', is_meal=False, qty=1, unit_price_gross=300, line_total_gross=300, meta={})
        build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        # At 20% VAT, gross 300 implies VAT ≈ 50 (since net ≈ 250)
        self.assertIn(rev.VAT, {50, 49}, 'Eatin should use EAT_VAT_CLASS=1 (20% rate) so VAT≈50p on £3.00')

    def test_meal_vat_takeaway_shake_zero_rate(self):
        # VAT: class 0 => 0%, class 1 => 20%
        PdVatTb.objects.all().delete()
        PdVatTb.objects.create(VAT_CLASS=0, VAT_RATE=0.0, VAT_DESC='Zero')
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')
        # Components: Cheeseburger(1/1), Fries(1/1), Strawberry Shake(EAT=1/TAKE=0)
        PdItem.objects.update_or_create(
            PRODNUMB=3,
            defaults=dict(
                PRODNAME='Cheeseburger', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=550, DC_VATPR=550,
                VATPR_2=550, DC_VATPR_2=550,
                VATPR_3=550, DC_VATPR_3=550,
                VATPR_4=550, DC_VATPR_4=550,
                VATPR_5=550, DC_VATPR_5=550,
                VATPR_6=550, DC_VATPR_6=550,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=30,
            defaults=dict(
                PRODNAME='Regular Fries', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=235, DC_VATPR=140,
                VATPR_2=235, DC_VATPR_2=140,
                VATPR_3=235, DC_VATPR_3=140,
                VATPR_4=235, DC_VATPR_4=140,
                VATPR_5=235, DC_VATPR_5=140,
                VATPR_6=235, DC_VATPR_6=140,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=900,
            defaults=dict(
                PRODNAME='Strawberry Shk', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=0,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=305, DC_VATPR=300,
                VATPR_2=305, DC_VATPR_2=300,
                VATPR_3=305, DC_VATPR_3=300,
                VATPR_4=305, DC_VATPR_4=300,
                VATPR_5=305, DC_VATPR_5=300,
                VATPR_6=305, DC_VATPR_6=300,
            )
        )
        # Create a takeaway meal order: total meal price = 550 + 140 + 300 = 990
        day = timezone.localdate() + timedelta(days=2)
        order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Cash', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(
            order=order, item_code=3, item_type='product', name='Cheeseburger Meal',
            variant_label='', is_meal=True, qty=1, unit_price_gross=990, line_total_gross=990,
            meta={'fries': 30, 'drink': 900, 'options': []}
        )
        build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        # Expected VAT for takeaway meal: Burger 550/6 ≈ 91.67, Fries 140/6 ≈ 23.33, Shake TAKE class 0 => 0. Total ≈ 115p
        self.assertIn(rev.VAT, {115, 114, 116})

    def test_meal_vat_eatin_shake_twenty_percent(self):
        # VAT: class 0 => 0%, class 1 => 20%
        PdVatTb.objects.all().delete()
        PdVatTb.objects.create(VAT_CLASS=0, VAT_RATE=0.0, VAT_DESC='Zero')
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Standard')
        # Components: Cheeseburger(1/1), Fries(1/1), Strawberry Shake(EAT=1/TAKE=0)
        PdItem.objects.update_or_create(
            PRODNUMB=3,
            defaults=dict(
                PRODNAME='Cheeseburger', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=550, DC_VATPR=550,
                VATPR_2=550, DC_VATPR_2=550,
                VATPR_3=550, DC_VATPR_3=550,
                VATPR_4=550, DC_VATPR_4=550,
                VATPR_5=550, DC_VATPR_5=550,
                VATPR_6=550, DC_VATPR_6=550,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=30,
            defaults=dict(
                PRODNAME='Regular Fries', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=235, DC_VATPR=140,
                VATPR_2=235, DC_VATPR_2=140,
                VATPR_3=235, DC_VATPR_3=140,
                VATPR_4=235, DC_VATPR_4=140,
                VATPR_5=235, DC_VATPR_5=140,
                VATPR_6=235, DC_VATPR_6=140,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=900,
            defaults=dict(
                PRODNAME='Strawberry Shk', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=0,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=305, DC_VATPR=300,
                VATPR_2=305, DC_VATPR_2=300,
                VATPR_3=305, DC_VATPR_3=300,
                VATPR_4=305, DC_VATPR_4=300,
                VATPR_5=305, DC_VATPR_5=300,
                VATPR_6=305, DC_VATPR_6=300,
            )
        )
        # Create an eat-in meal order: total meal price = 550 + 140 + 300 = 990
        day = timezone.localdate() + timedelta(days=3)
        order = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Cash', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(
            order=order, item_code=3, item_type='product', name='Cheeseburger Meal',
            variant_label='', is_meal=True, qty=1, unit_price_gross=990, line_total_gross=990,
            meta={'fries': 30, 'drink': 900, 'options': []}
        )
        build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        # Expected VAT for eat-in meal: Burger 550/6 ≈ 91.67, Fries 140/6 ≈ 23.33, Shake 300/6 = 50. Total ≈ 165p
        self.assertIn(rev.VAT, {165, 164, 166})
