import json

from django.urls import reverse

from ecommerce.tests.testcases import TestCase
from oscar.test.factories import ProductFactory, ProductClassFactory


class JournalProductViewTests(TestCase):

    def setUp(self):
        super(JournalProductViewTests, self).setUp()
        self.path = reverse('journal:api:v1:journal-list')
        self.product = ProductFactory(
            categories="",
            product_class=ProductClassFactory(
                name="Journal"
            )
        )

    def test_login_required(self):
        """ Users are required to login before accessing the view. """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 401)

    def test_journal_product_view(self):
        user = self.create_user(is_staff=True)
        self.client.login(username=user.username, password=self.password)
        response = self.client.get(self.path)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['count'], 1)
        self.assertEqual(response_data['results'][0]['product_class'], "Journal")
