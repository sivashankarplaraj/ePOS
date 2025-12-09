from django.test import TestCase
from django.urls import reverse
from update_till.models import PdItem, PdVatTb, AppProd, CompPro, OptPro
from manage_orders.models import Order, OrderLine
from manage_orders.services.daily_stats import build_daily_stats
from django.utils import timezone
from datetime import timedelta
import json


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


class PdMealAndComboOptionTests(TestCase):
    """
    PD file rules wiring tests:
    1) Product 71 Six Bites ordered as a meal should increment OPTION for chosen optional product (e.g., 27 Dip Mayo).
    2) If product 110 Dip None is chosen for combo 4 Sharing Platter, increment TAKEAWAY or EATIN basis accordingly.
    """
    def setUp(self):
        # Ensure VAT class exists
        PdVatTb.objects.get_or_create(VAT_CLASS=1, defaults={'VAT_RATE': 20.0, 'VAT_DESC': 'Standard'})
        # Minimal product setup used by daily_stats
        PdItem.objects.update_or_create(
            PRODNUMB=71,
            defaults=dict(
                PRODNAME='Six Bites', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=530, DC_VATPR=530,
                VATPR_2=530, DC_VATPR_2=530,
                VATPR_3=530, DC_VATPR_3=530,
                VATPR_4=530, DC_VATPR_4=530,
                VATPR_5=530, DC_VATPR_5=530,
                VATPR_6=530, DC_VATPR_6=530,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=30,
            defaults=dict(
                PRODNAME='Regular Fries', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=220, DC_VATPR=130,
                VATPR_2=220, DC_VATPR_2=130,
                VATPR_3=220, DC_VATPR_3=130,
                VATPR_4=220, DC_VATPR_4=130,
                VATPR_5=220, DC_VATPR_5=130,
                VATPR_6=220, DC_VATPR_6=130,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=52,
            defaults=dict(
                PRODNAME='Tango Can', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=140, DC_VATPR=140,
                VATPR_2=140, DC_VATPR_2=140,
                VATPR_3=140, DC_VATPR_3=140,
                VATPR_4=140, DC_VATPR_4=140,
                VATPR_5=140, DC_VATPR_5=140,
                VATPR_6=140, DC_VATPR_6=140,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=27,
            defaults=dict(
                PRODNAME='Dip Mayo', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=55, DC_VATPR=55,
                VATPR_2=55, DC_VATPR_2=55,
                VATPR_3=55, DC_VATPR_3=55,
                VATPR_4=55, DC_VATPR_4=55,
                VATPR_5=55, DC_VATPR_5=55,
                VATPR_6=55, DC_VATPR_6=55,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=110,
            defaults=dict(
                PRODNAME='Dip None', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=0, DC_VATPR=0,
                VATPR_2=0, DC_VATPR_2=0,
                VATPR_3=0, DC_VATPR_3=0,
                VATPR_4=0, DC_VATPR_4=0,
                VATPR_5=0, DC_VATPR_5=0,
                VATPR_6=0, DC_VATPR_6=0,
            )
        )
        PdItem.objects.update_or_create(
            PRODNUMB=4,
            defaults=dict(
                PRODNAME='Sharing Platter', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                VATPR=995, DC_VATPR=995,
                VATPR_2=995, DC_VATPR_2=995,
                VATPR_3=995, DC_VATPR_3=995,
                VATPR_4=995, DC_VATPR_4=995,
                VATPR_5=995, DC_VATPR_5=995,
                VATPR_6=995, DC_VATPR_6=995,
            )
        )

        # Combo relationships for Sharing Platter
        CompPro.objects.get_or_create(COMBONUMB=4, PRODNUMB=71, defaults={'T_PRODNUMB': 0})
        CompPro.objects.get_or_create(COMBONUMB=4, PRODNUMB=82, defaults={'T_PRODNUMB': 0})
        CompPro.objects.get_or_create(COMBONUMB=4, PRODNUMB=95, defaults={'T_PRODNUMB': 0})
        OptPro.objects.get_or_create(COMBONUMB=4, PRODNUMB=110, defaults={'T_PRODNUMB': 0})

    def test_meal_optional_increments_option_for_27(self):
        day = timezone.localdate()
        order = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Card', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        # Meal line for 71 with free choice 27 Dip Mayo
        OrderLine.objects.create(
            order=order,
            item_code=71,
            item_type='product',
            is_meal=True,
            qty=1,
            unit_price_gross=890,  # arbitrary meal price for test
            line_total_gross=890,
            meta={
                'fries': 30,
                'drink': 52,
                'free_choices': [27],
                'display_choices': ['Regular Fries','Tango Can','Free: Dip Mayo'],
                'meal_applied': True,
            },
        )
        build_daily_stats(day)
        from update_till.models import KPro
        k = KPro.objects.filter(stat_date=day, PRODNUMB=27, COMBO=False).first()
        self.assertIsNotNone(k, 'Expected KPro row for Dip Mayo (27)')
        self.assertEqual(k.OPTION, 1, 'Meal optional Dip Mayo should increment OPTION by 1')

    def test_combo_4_dip_none_counts_basis_takeaway_or_eatin(self):
        # Takeaway case
        day_take = timezone.localdate() + timedelta(days=10)
        order_take = Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Cash', created_at=timezone.make_aware(timezone.datetime.combine(day_take, timezone.datetime.min.time())))
        OrderLine.objects.create(order=order_take, item_code=4, item_type='combo', name='Sharing Platter', variant_label='', is_meal=False, qty=1, unit_price_gross=995, line_total_gross=995, meta={'options':[110]})
        build_daily_stats(day_take)
        from update_till.models import KPro
        dip_none_take = KPro.objects.get(stat_date=day_take, PRODNUMB=110, COMBO=False)
        self.assertEqual(dip_none_take.TAKEAWAY, 1, 'Dip None chosen in combo should count under TAKEAWAY for takeaway orders')
        # Eatin case
        day_eat = timezone.localdate() + timedelta(days=11)
        order_eat = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Cash', created_at=timezone.make_aware(timezone.datetime.combine(day_eat, timezone.datetime.min.time())))
        OrderLine.objects.create(order=order_eat, item_code=4, item_type='combo', name='Sharing Platter', variant_label='', is_meal=False, qty=1, unit_price_gross=995, line_total_gross=995, meta={'options':[110]})
        build_daily_stats(day_eat)
        dip_none_eat = KPro.objects.get(stat_date=day_eat, PRODNUMB=110, COMBO=False)
        self.assertEqual(dip_none_eat.EATIN, 1, 'Dip None chosen in combo should count under EATIN for eat-in orders')

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


class ChannelMappingTests(TestCase):
    """Tests for /api/channels endpoint after migration to PriceBand."""
    def setUp(self):
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Std')
        from update_till.models import PriceBand
        # APPLY_HERE True rows
        PriceBand.objects.create(
            PRICE_ID=1, PRICE_SUB_ID=0, SEQ_ORDER=1, SUPPLIER_CODE='OT-C', SUPPLIER_NAME='Standard',
            APPLY_HERE=True, PARENT_ID=1, ACC_FIRM_NUM=0,
            ACCEPT_CASH=True, ACCEPT_CARD=True, ACCEPT_ONACC=False,
            ACCEPT_COOKED_WASTE=True, ACCEPT_CREW_FOOD=True, ACCEPT_VOUCHER=True,
            DELIV_SUPPLIER=False,
            HOT_DRINK=True
        )
        PriceBand.objects.create(
            PRICE_ID=6, PRICE_SUB_ID=0, SEQ_ORDER=2, SUPPLIER_CODE='JE-D', SUPPLIER_NAME='Just Eat - Deliver',
            APPLY_HERE=True, PARENT_ID=3, ACC_FIRM_NUM=0,
            ACCEPT_CASH=False, ACCEPT_CARD=True, ACCEPT_ONACC=False,
            ACCEPT_COOKED_WASTE=False, ACCEPT_CREW_FOOD=False, ACCEPT_VOUCHER=False,
            DELIV_SUPPLIER=True,
            HOT_DRINK=False
        )
        # APPLY_HERE False row (should be filtered out)
        PriceBand.objects.create(
            PRICE_ID=2, PRICE_SUB_ID=0, SEQ_ORDER=3, SUPPLIER_CODE='XX-C', SUPPLIER_NAME='Hidden Channel',
            APPLY_HERE=False, PARENT_ID=9, ACC_FIRM_NUM=0,
            ACCEPT_CASH=True, ACCEPT_CARD=True, ACCEPT_ONACC=False,
            ACCEPT_COOKED_WASTE=False, ACCEPT_CREW_FOOD=False, ACCEPT_VOUCHER=False,
            DELIV_SUPPLIER=False,
            HOT_DRINK=True
        )

    def test_api_channels_filters_and_maps_fields(self):
        resp = self.client.get(reverse('mo_api_channels'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['channels']
        # Hidden channel excluded
        codes = [c['channel_code'] for c in data]
        self.assertNotIn('XX-C', codes)
        # Present codes
        self.assertIn('OT-C', codes)
        self.assertIn('JE-D', codes)
        # Field mapping and ordering (SEQ_ORDER ascending)
        self.assertGreaterEqual(len(data), 2)
        self.assertEqual(data[0]['channel_code'], 'OT-C')  # SEQ_ORDER 1 first
        standard = next(c for c in data if c['channel_code'] == 'OT-C')
        justeat = next(c for c in data if c['channel_code'] == 'JE-D')
        # band mapping
        self.assertEqual(standard['band'], 1)
        self.assertEqual(justeat['band'], 6)
        # co_number from PARENT_ID stringified
        self.assertEqual(standard['co_number'], '1')
        self.assertEqual(justeat['co_number'], '3')
        # is_third_party_delivery is inverse of HOT_DRINK
        self.assertFalse(standard['is_third_party_delivery'])  # HOT_DRINK True -> False
        self.assertTrue(justeat['is_third_party_delivery'])    # HOT_DRINK False -> True


class BandCoNumberValidationTests(TestCase):
    """Tests for band_co_number validation using dynamic PriceBand PARENT_ID codes."""
    def setUp(self):
        PdVatTb.objects.create(VAT_CLASS=1, VAT_RATE=20.0, VAT_DESC='Std')
        from update_till.models import PriceBand
        PriceBand.objects.create(
            PRICE_ID=1, PRICE_SUB_ID=0, SEQ_ORDER=1, SUPPLIER_CODE='OT-C', SUPPLIER_NAME='Standard',
            APPLY_HERE=True, PARENT_ID=77, ACC_FIRM_NUM=0,
            ACCEPT_CASH=True, ACCEPT_CARD=True, ACCEPT_ONACC=False,
            ACCEPT_COOKED_WASTE=True, ACCEPT_CREW_FOOD=True, ACCEPT_VOUCHER=True,
            DELIV_SUPPLIER=False,
            HOT_DRINK=True
        )
        _mk_product(1001, 'Test Prod', 250, dc=250)

    def test_submit_order_with_valid_band_co_number(self):
        payload = {
            'price_band': '1', 'vat_basis': 'take', 'show_net': False,
            'band_co_number': 'Standard',
            'lines': [{
                'code': 1001, 'type': 'product', 'name': 'Test Prod', 'variant': None,
                'meal': False, 'qty': 1, 'price_gross': 250, 'meta': {}
            }]
        }
        resp = self.client.post(reverse('mo_api_submit_order'), data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()['total_gross'], 250)

    def test_submit_order_with_invalid_band_co_number(self):
        payload = {
            'price_band': '1', 'vat_basis': 'take', 'show_net': False,
            'band_co_number': 'ZZZZ',  # not in static mapping or PriceBand PARENT_ID
            'lines': [{
                'code': 1001, 'type': 'product', 'name': 'Test Prod', 'variant': None,
                'meal': False, 'qty': 1, 'price_gross': 250, 'meta': {}
            }]
        }
        resp = self.client.post(reverse('mo_api_submit_order'), data=payload, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Invalid band_co_number', resp.content.decode('utf-8'))


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
        # Validate KRev combination discount (EX-VAT): previously 225 gross; now ex-VAT rounds to 21
        from update_till.models import KRev, KPro
        rev = KRev.objects.get(stat_date=timezone.localdate())
        self.assertEqual(rev.TDISCNTVA, 21)
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
        # Effective meal price uses discounted components: 505 + 170 + 280 = 955; singles total 505+250+285=1040; ex-VAT discount rounds to 71
        OrderLine.objects.create(order=order, item_code=3, item_type='product', name='Cheeseburger Meal', variant_label='', is_meal=True, qty=1, unit_price_gross=955, line_total_gross=955, meta={'fries':31, 'drink':69, 'go_large': True})
        build_daily_stats(timezone.localdate())
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=timezone.localdate())
        self.assertEqual(rev.TMEAL_DISCNT, 71)
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


class PaidOutRevenueTests(TestCase):
    def setUp(self):
        # Ensure a default VAT class exists even though it won't be used by Paid Out (no lines)
        PdVatTb.objects.get_or_create(VAT_CLASS=1, defaults={'VAT_RATE': 20.0, 'VAT_DESC': 'Standard'})

    def test_paid_out_affects_krev_and_cash(self):
        # Create a simple cash order for today (no lines needed for KRev cash accumulation)
        now = timezone.now()
        Order.objects.create(
            created_at=now, completed_at=now, status='dispatched',
            price_band=1, vat_basis='take', show_net=False,
            total_gross=1000, total_net=900, payment_method='Cash', crew_id='0'
        )
        # Record a Paid Out of 300 pence via API
        payload = { 'price_band': '1', 'band_co_number': '', 'amount_pence': 300, 'notes': 'petty cash' }
        resp = self.client.post(reverse('mo_api_paid_out'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json().get('status'), 'ok')
        # Build daily stats for today and check KRev
        stats = build_daily_stats(export_date=now.date())
        self.assertEqual(stats.rev.get('TCASHVAL'), 700)
        self.assertEqual(stats.rev.get('TPAYOUTVA'), 300)
        # Verify Paid Out order stored amount in total_gross (new spec)
        paid_out_order = Order.objects.filter(payment_method='Paid Out').order_by('-id').first()
        self.assertIsNotNone(paid_out_order)
        self.assertEqual(paid_out_order.total_gross, 300)
        self.assertEqual(paid_out_order.total_net, 0)


class UsInfoPackParityTests(TestCase):
    """Parity tests against Uncle Sams info pack scenarios (2025-12-03)."""
    def setUp(self):
        # VAT class 1 = 20%
        PdVatTb.objects.update_or_create(VAT_CLASS=1, defaults={'VAT_RATE': 20.0, 'VAT_DESC': 'Std'})

    def test_crew_meal_discount_and_staff_value(self):
        # Prices per doc (incl VAT): Burger 550, Fries (meal) 140 vs single 235, Shake (meal) 300 vs single 305
        PdItem.objects.update_or_create(
            PRODNUMB=3,
            defaults=dict(PRODNAME='Cheeseburger', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                          READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                          VATPR=550, DC_VATPR=550,
                          VATPR_2=550, DC_VATPR_2=550,
                          VATPR_3=550, DC_VATPR_3=550,
                          VATPR_4=550, DC_VATPR_4=550,
                          VATPR_5=550, DC_VATPR_5=550,
                          VATPR_6=550, DC_VATPR_6=550)
        )
        PdItem.objects.update_or_create(
            PRODNUMB=30,
            defaults=dict(PRODNAME='Regular Fries', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                          READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                          VATPR=235, DC_VATPR=140,
                          VATPR_2=235, DC_VATPR_2=140,
                          VATPR_3=235, DC_VATPR_3=140,
                          VATPR_4=235, DC_VATPR_4=140,
                          VATPR_5=235, DC_VATPR_5=140,
                          VATPR_6=235, DC_VATPR_6=140)
        )
        PdItem.objects.update_or_create(
            PRODNUMB=62,
            defaults=dict(PRODNAME='Strawberry Shk', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                          READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                          VATPR=305, DC_VATPR=300,
                          VATPR_2=305, DC_VATPR_2=300,
                          VATPR_3=305, DC_VATPR_3=300,
                          VATPR_4=305, DC_VATPR_4=300,
                          VATPR_5=305, DC_VATPR_5=300,
                          VATPR_6=305, DC_VATPR_6=300)
        )
        day = timezone.localdate() + timedelta(days=20)
        o = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Crew Food', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        # Meal line (total 550 + 140 + 300 = 990)
        OrderLine.objects.create(order=o, item_code=3, item_type='product', name='Cheeseburger Meal', variant_label='', is_meal=True, qty=1, unit_price_gross=990, line_total_gross=990, meta={'fries':30,'drink':62})
        s = build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        self.assertEqual(rev.TSTAFFVAL, 825, 'Crew Food staff value should be meal ex-VAT total (8.25)')
        self.assertEqual(rev.TMEAL_DISCNT, 83, 'Meal discount should be singles ex-VAT (9.08) minus meal ex-VAT (8.25)')

    def test_crew_combo_sharing_platter_discount_and_value(self):
        # Component products (incl VAT)
        PdItem.objects.update_or_create(PRODNUMB=26, defaults=dict(PRODNAME='Dip Ketchup', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                    VATPR=35, DC_VATPR=35, VATPR_2=35, DC_VATPR_2=35, VATPR_3=35, DC_VATPR_3=35, VATPR_4=35, DC_VATPR_4=35, VATPR_5=35, DC_VATPR_5=35, VATPR_6=35, DC_VATPR_6=35))
        PdItem.objects.update_or_create(PRODNUMB=28, defaults=dict(PRODNAME='Dip Chilli', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=65, DC_VATPR=65, VATPR_2=65, DC_VATPR_2=65, VATPR_3=65, DC_VATPR_3=65, VATPR_4=65, DC_VATPR_4=65, VATPR_5=65, DC_VATPR_5=65, VATPR_6=65, DC_VATPR_6=65))
        PdItem.objects.update_or_create(PRODNUMB=71, defaults=dict(PRODNAME='Six Bites', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=560, DC_VATPR=560, VATPR_2=560, DC_VATPR_2=560, VATPR_3=560, DC_VATPR_3=560, VATPR_4=560, DC_VATPR_4=560, VATPR_5=560, DC_VATPR_5=560, VATPR_6=560, DC_VATPR_6=560))
        PdItem.objects.update_or_create(PRODNUMB=82, defaults=dict(PRODNAME='Onion Rings 8', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=260, DC_VATPR=260, VATPR_2=260, DC_VATPR_2=260, VATPR_3=260, DC_VATPR_3=260, VATPR_4=260, DC_VATPR_4=260, VATPR_5=260, DC_VATPR_5=260, VATPR_6=260, DC_VATPR_6=260))
        PdItem.objects.update_or_create(PRODNUMB=95, defaults=dict(PRODNAME='Mozarela Fingers', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=335, DC_VATPR=335, VATPR_2=335, DC_VATPR_2=335, VATPR_3=335, DC_VATPR_3=335, VATPR_4=335, DC_VATPR_4=335, VATPR_5=335, DC_VATPR_5=335, VATPR_6=335, DC_VATPR_6=335))
        # Combo record (incl VAT): Sharing Platter 10.05
        from update_till.models import CombTb
        CombTb.objects.update_or_create(COMBONUMB=4, defaults=dict(DESC='Sharing Platter', T_COMB_NUM=0, EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                                                                    VATPR=1005, T_VATPR=1005, VATPR_2=1005, T_VATPR_2=1005, VATPR_3=1005, T_VATPR_3=1005, VATPR_4=1005, T_VATPR_4=1005, VATPR_5=1005, T_VATPR_5=1005, VATPR_6=1005, T_VATPR_6=1005))
        # Relationships
        CompPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=71, defaults={'T_PRODNUMB': 0})
        CompPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=82, defaults={'T_PRODNUMB': 0})
        CompPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=95, defaults={'T_PRODNUMB': 0})
        OptPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=26, defaults={'T_PRODNUMB': 0})
        OptPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=28, defaults={'T_PRODNUMB': 0})
        day = timezone.localdate() + timedelta(days=21)
        o = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Crew Food', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=o, item_code=4, item_type='combo', name='Sharing Platter', variant_label='', is_meal=False, qty=1, unit_price_gross=1005, line_total_gross=1005, meta={'options':[26,28]})
        s = build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        self.assertEqual(rev.TSTAFFVAL, 838, 'Crew Food combo staff value should be combo ex-VAT total (8.38)')
        self.assertEqual(rev.TDISCNTVA, 208, 'Combo discount should be components ex-VAT sum (10.46) minus combo ex-VAT (8.38)')

    def test_cooked_waste_mirrors_values(self):
        # Define products as per doc
        PdItem.objects.update_or_create(
            PRODNUMB=3,
            defaults=dict(PRODNAME='Cheeseburger', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                          READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                          VATPR=550, DC_VATPR=550,
                          VATPR_2=550, DC_VATPR_2=550,
                          VATPR_3=550, DC_VATPR_3=550,
                          VATPR_4=550, DC_VATPR_4=550,
                          VATPR_5=550, DC_VATPR_5=550,
                          VATPR_6=550, DC_VATPR_6=550)
        )
        PdItem.objects.update_or_create(
            PRODNUMB=30,
            defaults=dict(PRODNAME='Regular Fries', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                          READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                          VATPR=235, DC_VATPR=140,
                          VATPR_2=235, DC_VATPR_2=140,
                          VATPR_3=235, DC_VATPR_3=140,
                          VATPR_4=235, DC_VATPR_4=140,
                          VATPR_5=235, DC_VATPR_5=140,
                          VATPR_6=235, DC_VATPR_6=140)
        )
        PdItem.objects.update_or_create(
            PRODNUMB=62,
            defaults=dict(PRODNAME='Strawberry Shk', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                          READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                          VATPR=305, DC_VATPR=300,
                          VATPR_2=305, DC_VATPR_2=300,
                          VATPR_3=305, DC_VATPR_3=300,
                          VATPR_4=305, DC_VATPR_4=300,
                          VATPR_5=305, DC_VATPR_5=300,
                          VATPR_6=305, DC_VATPR_6=300)
        )
        PdItem.objects.update_or_create(PRODNUMB=26, defaults=dict(PRODNAME='Dip Ketchup', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                    VATPR=35, DC_VATPR=35, VATPR_2=35, DC_VATPR_2=35, VATPR_3=35, DC_VATPR_3=35, VATPR_4=35, DC_VATPR_4=35, VATPR_5=35, DC_VATPR_5=35, VATPR_6=35, DC_VATPR_6=35))
        PdItem.objects.update_or_create(PRODNUMB=28, defaults=dict(PRODNAME='Dip Chilli', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=65, DC_VATPR=65, VATPR_2=65, DC_VATPR_2=65, VATPR_3=65, DC_VATPR_3=65, VATPR_4=65, DC_VATPR_4=65, VATPR_5=65, DC_VATPR_5=65, VATPR_6=65, DC_VATPR_6=65))
        PdItem.objects.update_or_create(PRODNUMB=71, defaults=dict(PRODNAME='Six Bites', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=560, DC_VATPR=560, VATPR_2=560, DC_VATPR_2=560, VATPR_3=560, DC_VATPR_3=560, VATPR_4=560, DC_VATPR_4=560, VATPR_5=560, DC_VATPR_5=560, VATPR_6=560, DC_VATPR_6=560))
        # Additional combo component products needed for combo discount math
        PdItem.objects.update_or_create(PRODNUMB=82, defaults=dict(PRODNAME='Onion Rings 8', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=260, DC_VATPR=260, VATPR_2=260, DC_VATPR_2=260, VATPR_3=260, DC_VATPR_3=260, VATPR_4=260, DC_VATPR_4=260, VATPR_5=260, DC_VATPR_5=260, VATPR_6=260, DC_VATPR_6=260))
        PdItem.objects.update_or_create(PRODNUMB=95, defaults=dict(PRODNAME='Mozarela Fingers', EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1, READBACK_ORD=1, MEAL_ONLY=False, MEAL_CODE=0, MEAL_DRINK=0, T_DRINK_CD=0,
                                                                   VATPR=335, DC_VATPR=335, VATPR_2=335, DC_VATPR_2=335, VATPR_3=335, DC_VATPR_3=335, VATPR_4=335, DC_VATPR_4=335, VATPR_5=335, DC_VATPR_5=335, VATPR_6=335, DC_VATPR_6=335))
        from update_till.models import CombTb
        CombTb.objects.update_or_create(COMBONUMB=4, defaults=dict(DESC='Sharing Platter', T_COMB_NUM=0, EAT_VAT_CLASS=1, TAKE_VAT_CLASS=1,
                                                                    VATPR=1005, T_VATPR=1005, VATPR_2=1005, T_VATPR_2=1005, VATPR_3=1005, T_VATPR_3=1005, VATPR_4=1005, T_VATPR_4=1005, VATPR_5=1005, T_VATPR_5=1005, VATPR_6=1005, T_VATPR_6=1005))
        # Relationships for combo components and options
        CompPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=71, defaults={'T_PRODNUMB': 0})
        CompPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=82, defaults={'T_PRODNUMB': 0})
        CompPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=95, defaults={'T_PRODNUMB': 0})
        OptPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=26, defaults={'T_PRODNUMB': 0})
        OptPro.objects.update_or_create(COMBONUMB=4, PRODNUMB=28, defaults={'T_PRODNUMB': 0})

        day = timezone.localdate() + timedelta(days=22)
        ow = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Waste food', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=ow, item_code=3, item_type='product', name='Cheeseburger Meal', variant_label='', is_meal=True, qty=1, unit_price_gross=990, line_total_gross=990, meta={'fries':30,'drink':62})
        # Combo waste
        ow2 = Order.objects.create(price_band=1, vat_basis='eat', show_net=False, payment_method='Waste food', created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        OrderLine.objects.create(order=ow2, item_code=4, item_type='combo', name='Sharing Platter', variant_label='', is_meal=False, qty=1, unit_price_gross=1005, line_total_gross=1005, meta={'options':[26,28]})
        build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        self.assertEqual(rev.TWASTEVAL, 825 + 838, 'Waste totals should reflect meal (8.25) + combo (8.38) ex-VAT values')
        self.assertEqual(rev.TMEAL_DISCNT, 83)
        self.assertEqual(rev.TDISCNTVA, 208)

    def test_voucher_mapping_to_token_fields(self):
        day = timezone.localdate() + timedelta(days=23)
        # Simple voucher-only payment
        Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Voucher', total_gross=500, created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        # Split payment including voucher
        Order.objects.create(price_band=1, vat_basis='take', show_net=False, payment_method='Split', split_cash_pence=100, split_card_pence=200, split_voucher_pence=300, total_gross=600, created_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())))
        build_daily_stats(day)
        from update_till.models import KRev
        rev = KRev.objects.get(stat_date=day)
        self.assertEqual(rev.TTOKENVAL, 500 + 300)
        self.assertEqual(rev.TCOUPVAL, 0)
        self.assertEqual(rev.TCASHVAL, 100)
        self.assertEqual(rev.TCARDVAL, 200)
