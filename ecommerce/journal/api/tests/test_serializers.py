"""
Test cases to cover JournalProductSerializer.
"""
from oscar.core.loading import get_model
from ecommerce.tests.testcases import TestCase

from oscar.test.factories import ProductFactory, ProductClassFactory, ProductAttributeFactory, \
    ProductAttributeValueFactory
from ecommerce.tests.factories import StockRecordFactory, PartnerFactory
from ecommerce.journal.api.serializers import JournalProductSerializer, StockRecordSerializer, AttributesSerializer

StockRecord = get_model('partner', 'StockRecord')


class AttributesSerializerTest(TestCase):
    def setUp(self):
        super(AttributesSerializerTest, self).setUp()
        self.expected_data = {
            'code': 'weight',
            'name': 'weight',
            'value': '0.2'
        }

    def test_serializer_data(self):
        """
        Test serializer return data properly.
        """
        product_attribute_value = ProductAttributeValueFactory(
            value=0.2,
            product=ProductFactory(
                categories=""
            )
        )
        data = AttributesSerializer(product_attribute_value).data
        self.assertEqual(data, self.expected_data)


class StockRecordSerializerTest(TestCase):
    def setUp(self):
        super(StockRecordSerializerTest, self).setUp()
        self.expected_data = {
            'partner': 'dummy-partner',
            'partner_sku': 'unit02',
            'price_excl_tax': '9.99',
            'price_currency': 'USD'
        }

    def test_serializer_data(self):
        """
        Test serializer return data properly.
        """
        stock_record = StockRecordFactory(
            partner_sku="unit02",
            partner=PartnerFactory(
                short_code="dummy-partner"
            ),
            product=ProductFactory(
                categories=""
            )
        )
        data = StockRecordSerializer(stock_record).data
        self.assertEqual(data, self.expected_data)


class JournalProductSerializerTest(TestCase):
    def setUp(self):
        super(JournalProductSerializerTest, self).setUp()
        self.expected_data = {
            'attribute_values': [],
            'stockrecords': [],
            'product_class': 'Journal',
            'title': 'A confederacy of dunces',
            'expires': None,
            'id': 1,
            'structure': 'standalone'
        }

    def test_serializer_data(self):
        """
        Test serializer return data properly.
        """
        product = ProductFactory(
            product_class=ProductClassFactory(
                name="Journal"
            ),
            stockrecords=[],
            categories=""
        )
        data = JournalProductSerializer(product).data
        self.assertEqual(data, self.expected_data)

    def _create_data(self):
        product_class=ProductClassFactory(
            name="Journal",
            requires_shipping=False,
            track_stock=False
        )
        ProductAttributeFactory(
            product_class=product_class
        )
        return {
            'attribute_values': [],
            'stockrecords': [
                StockRecordFactory()
            ],
            'product_class': product_class,
            'title': 'A confederacy of dunces',
            'expires': None,
            'id': 1,
            'structure': 'standalone'
        }

    # def test_serializer_create(self):
    #     """
    #     Test serializer return data properly.
    #     """
    #     # TODO: need to finish this in right way.
    #     product = JournalProductSerializer().create(self._create_data())