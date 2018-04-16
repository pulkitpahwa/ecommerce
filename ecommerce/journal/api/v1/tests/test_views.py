import json
from django.urls import reverse

from ecommerce.tests.testcases import TestCase
from oscar.test.factories import ProductFactory, ProductClassFactory


class JournalProductViewTests(TestCase):

    def setUp(self):
        super(JournalProductViewTests, self).setUp()
        self.path = reverse('journal:api:v1:journal-list')
        self.product = ProductFactory(
            product_class=ProductClassFactory(
                name="Journal",
                requires_shipping=False,
                track_stock=False
            )
        )

    def test_journal_product_view(self):
        response = self.client.get(self.path)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['count'], 1)
        self.assertEqual(response_data['results'][0]['product_class'], "Journal")


