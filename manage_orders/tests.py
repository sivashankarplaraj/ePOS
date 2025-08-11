from django.test import TestCase, Client
from django.urls import reverse

class ManageOrdersBasicTests(TestCase):
    def test_index_redirects_to_order(self):
        resp = self.client.get(reverse('manage_orders_index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Create Order', resp.content)
        self.assertIn(b'Uncle Sam', resp.content)

    def test_order_url(self):
        resp = self.client.get(reverse('manage_orders_order'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Price Band', resp.content)
