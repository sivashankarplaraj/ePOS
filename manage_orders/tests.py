from django.test import TestCase
from django.urls import reverse
from update_till.models import PdItem, PdVatTb, AppProd


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
