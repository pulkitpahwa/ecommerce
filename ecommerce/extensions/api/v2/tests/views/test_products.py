from __future__ import unicode_literals
import datetime
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from oscar.core.loading import get_model
import pytz

from ecommerce.courses.models import Course
from ecommerce.extensions.api.v2.tests.views import JSON_CONTENT_TYPE, ProductSerializerMixin
from ecommerce.extensions.catalogue.tests.mixins import CourseCatalogTestMixin
from ecommerce.tests.mixins import UserMixin, PartnerMixin

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')


class ProductViewSetTests(ProductSerializerMixin, CourseCatalogTestMixin, UserMixin, PartnerMixin, TestCase):
    maxDiff = None

    def setUp(self):
        super(ProductViewSetTests, self).setUp()
        self.user = self.create_user(is_staff=True)
        self.client.login(username=self.user.username, password=self.password)
        self.course = Course.objects.create(id='edX/DemoX/Demo_Course', name='Test Course')
        self.partner = self.create_partner('edx')

        # TODO Update the expiration date by 2099-12-31
        expires = datetime.datetime(2100, 1, 1, tzinfo=pytz.UTC)
        self.seat = self.course.create_or_update_seat('honor', False, 0, self.partner, expires=expires)

    def test_list(self):
        """ Verify a list of products is returned. """
        path = reverse('api:v2:product-list')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        results = [self.serialize_product(p) for p in self.course.products.all()]
        expected = {'count': 2, 'next': None, 'previous': None, 'results': results}
        self.assertDictEqual(json.loads(response.content), expected)

        # If no products exist, the view should return an empty result set.
        Product.objects.all().delete()
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        expected = {'count': 0, 'next': None, 'previous': None, 'results': []}
        self.assertDictEqual(json.loads(response.content), expected)

    def test_retrieve(self):
        """ Verify a single product is returned. """
        path = reverse('api:v2:product-detail', kwargs={'pk': 999})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

        path = reverse('api:v2:product-detail', kwargs={'pk': self.seat.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), self.serialize_product(self.seat))

    def test_destroy(self):
        """ Verify the view does NOT allow products to be destroyed. """
        product_id = self.seat.id
        path = reverse('api:v2:product-detail', kwargs={'pk': product_id})
        response = self.client.delete(path)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Product.objects.filter(id=product_id).exists())

    def test_update(self):
        """ Verify the view allows individual products to be updated. """
        data = self.serialize_product(self.seat)
        data['title'] = 'Fake Seat Title'

        path = reverse('api:v2:product-detail', kwargs={'pk': self.seat.id})
        response = self.client.put(path, json.dumps(data), JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200, response.content)

        product = Product.objects.get(id=self.seat.id)
        self.assertEqual(product.title, data['title'])
        self.assertDictEqual(json.loads(response.content), self.serialize_product(product))

    def test_list_for_course(self):
        """ Verify the view supports listing products for a single course. """
        # Create another course and seat to confirm filtering.
        other_course = Course.objects.create(id='edX/DemoX/XYZ', name='Test Course 2')
        other_course.create_or_update_seat('honor', False, 0, self.partner)

        path = reverse('api:v2:course-product-list', kwargs={'parent_lookup_course_id': self.course.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        results = [self.serialize_product(p) for p in self.course.products.all()]
        expected = {'count': 2, 'next': None, 'previous': None, 'results': results}
        self.assertDictEqual(json.loads(response.content), expected)

    def test_get_partner_products(self):
        """Verify the endpoint returns the list of products associated with a
        partner.
        """
        url = reverse(
            'api:v2:partner-product-list',
            kwargs={'parent_lookup_stockrecords__partner_id': self.partner.id}
        )
        response = self.client.get(url)
        expected_data = self.serialize_product(self.seat)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(json.loads(response.content)['results'], [expected_data])

    def test_no_partner_product(self):
        """Verify the endpoint returns an empty list if no products are
        associated with a partner.
        """
        Product.objects.all().delete()
        url = reverse(
            'api:v2:partner-product-list',
            kwargs={'parent_lookup_stockrecords__partner_id': self.partner.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }
        self.assertDictEqual(json.loads(response.content), expected)
