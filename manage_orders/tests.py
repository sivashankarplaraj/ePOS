from django.test import TestCase
from django.urls import reverse
from update_till.models import PdItem, PdVatTb, AppProd, CompPro, OptPro
from manage_orders.models import Order, OrderLine
from manage_orders.services.daily_stats import build_daily_stats
from django.utils import timezone


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
        # WASTE count for product 71
        prod_row = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=71, COMBO=False)
        self.assertEqual(prod_row.WASTE, 1)
        # OPTION count for dips (26 and 39)
        dip26 = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=26, COMBO=False)
        dip39 = KPro.objects.get(stat_date=timezone.localdate(), PRODNUMB=39, COMBO=False)
        self.assertEqual(dip26.OPTION, 1)
        self.assertEqual(dip39.OPTION, 1)

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
