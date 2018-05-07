# -*- coding: utf-8 -*-
import uuid

import httpretty
from oscar.core.loading import get_model

from oscar.test.factories import ConditionalOfferFactory
from ecommerce.programs.constants import BENEFIT_MAP
from ecommerce.programs.custom import class_path
from ecommerce.extensions.test.factories import PercentageDiscountBenefitWithoutRangeFactory, ConditionalOfferFactory,\
    JournalConditionalFactory
from ecommerce.journal.forms import JournalOfferForm
from ecommerce.tests.testcases import TestCase

Benefit = get_model('offer', 'Benefit')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


class JournalOfferFormTests(TestCase):
    def generate_data(self, **kwargs):
        data = {
            'journal_bundle_uuid': uuid.uuid4(),
            'benefit_type': Benefit.PERCENTAGE,
            'benefit_value': 22,
        }
        data.update(**kwargs)
        return data

    # def assert_program_offer_conditions(self, offer, program_uuid, expected_benefit_value, expected_benefit_type,
    #                                     expected_name):
    #     """ Assert the given offer's parameters match the expected values. """
    #     self.assertEqual(str(offer.name), expected_name)
    #     self.assertEqual(offer.offer_type, ConditionalOffer.SITE)
    #     self.assertEqual(offer.status, ConditionalOffer.OPEN)
    #     self.assertEqual(offer.max_basket_applications, 1)
    #     self.assertEqual(offer.site, self.site)
    #     self.assertEqual(offer.condition.program_uuid, program_uuid)
    #     self.assertEqual(offer.benefit.proxy_class, class_path(BENEFIT_MAP[expected_benefit_type]))
    #     self.assertEqual(offer.benefit.value, expected_benefit_value)
    #
    def assert_form_errors(self, data, expected_errors):
        """ Assert that form validation fails with the expected errors. """
        form = JournalOfferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, expected_errors)

    def test_init(self):
        """ The constructor should pull initial data from the passed-in instance. """
        journal_offer = ConditionalOfferFactory(
            benefit=PercentageDiscountBenefitWithoutRangeFactory(),
            condition=JournalConditionalFactory()
        )
        form = JournalOfferForm(instance=journal_offer)
        self.assertEqual(form['journal_bundle_uuid'].value(), journal_offer.condition.journal_bundle_uuid.hex)
        self.assertEqual(form['benefit_type'].value(), journal_offer.benefit.proxy().benefit_class_type)
        self.assertEqual(form['benefit_value'].value(), journal_offer.benefit.value)

    def test_clean_percentage(self):
        """ If a percentage benefit type is specified, the benefit value must never be greater than 100. """
        data = self.generate_data(benefit_type=Benefit.PERCENTAGE, benefit_value=101)
        self.assert_form_errors(data, {'benefit_value': ['Percentage discounts cannot be greater than 100%.']})

    def test_clean_with_missing_start_date(self):
        """ If an end date is specified, a start date must also be specified. """
        data = self.generate_data(end_datetime='2017-01-01 00:00:00')
        self.assert_form_errors(data,
                                {'start_datetime': ['A start date must be specified when specifying an end date']})

    def test_clean_with_invalid_date_ordering(self):
        """ The start date must always occur before the end date. """
        data = self.generate_data(start_datetime='2017-01-02 00:00:00', end_datetime='2017-01-01 00:00:00')
        self.assert_form_errors(data, {'start_datetime': ['The start date must occur before the end date']})

    def test_clean_with_conflicting_journal_uuid(self):
        """ If an offer already exists for the given program, an error should be raised. """
        journal_offer = ConditionalOfferFactory(
            benefit=PercentageDiscountBenefitWithoutRangeFactory(),
            condition=JournalConditionalFactory()
        )
        data = self.generate_data(journal_bundle_uuid=journal_offer.condition.journal_bundle_uuid)
        self.assert_form_errors(data, {'journal_bundle_uuid': ['An offer already exists for this journal bundle']})

    # @httpretty.activate
    # def test_save_create(self):
    #     """ A new ConditionalOffer, Benefit, and Condition should be created. """
    #     data = self.generate_data()
    #     self.mock_program_detail_endpoint(data['program_uuid'], self.site_configuration.discovery_api_url)
    #     form = JournalOfferForm(request=self.request, data=data)
    #     form.is_valid()
    #     offer = form.save()
    #     self.assert_program_offer_conditions(offer, data['program_uuid'], data['benefit_value'], data['benefit_type'],
    #                                          'Discount for the Test Program MicroMockers Program')
    #
    # @httpretty.activate
    # def test_save_create_special_char_title(self):
    #     """ When the title is international, A new ConditionalOffer, Benefit, and Condition should still be created."""
    #     data = self.generate_data()
    #     self.mock_program_detail_endpoint(data['program_uuid'],
    #                                       self.site_configuration.discovery_api_url,
    #                                       title=u'Sp\xe1nish Program')
    #     form = ProgramOfferForm(request=self.request, data=data)
    #     form.is_valid()
    #     offer = form.save()
    #     self.assert_program_offer_conditions(offer, data['program_uuid'], data['benefit_value'], data['benefit_type'],
    #                                          'Discount for the Spánish Program MicroMockers Program')
    #
    # @httpretty.activate
    # def test_save_edit(self):
    #     """ Previously-created ConditionalOffer, Benefit, and Condition instances should be updated. """
    #     offer = factories.ProgramOfferFactory()
    #     data = self.generate_data(program_uuid=offer.condition.program_uuid, benefit_type=Benefit.FIXED)
    #     self.mock_program_detail_endpoint(data['program_uuid'], self.site_configuration.discovery_api_url)
    #     form = ProgramOfferForm(request=self.request, data=data, instance=offer)
    #     form.is_valid()
    #     form.save()
    #
    #     offer.refresh_from_db()
    #     self.assert_program_offer_conditions(offer, data['program_uuid'], data['benefit_value'], data['benefit_type'],
    #                                          'Discount for the Test Program MicroMockers Program')
    #
    # @httpretty.activate
    # def test_save_without_commit(self):
    #     """ No data should be persisted to the database if the commit kwarg is set to False. """
    #     data = self.generate_data()
    #     form = ProgramOfferForm(request=self.request, data=data)
    #     self.mock_program_detail_endpoint(data['program_uuid'], self.site_configuration.discovery_api_url)
    #     form.is_valid()
    #     instance = form.save(commit=False)
    #     self.assertIsNone(instance.pk)
    #     self.assertFalse(hasattr(instance, 'benefit'))
    #     self.assertFalse(hasattr(instance, 'condition'))
    #
    # @httpretty.activate
    # def test_save_offer_name(self):
    #     """ If a request object is sent, the offer name should include program title and type. """
    #     data = self.generate_data()
    #     self.mock_program_detail_endpoint(data['program_uuid'], self.site_configuration.discovery_api_url)
    #     form = ProgramOfferForm(request=self.request, data=data)
    #     form.is_valid()
    #     offer = form.save()
    #     self.assert_program_offer_conditions(offer, data['program_uuid'], data['benefit_value'], data['benefit_type'],
    #                                          'Discount for the Test Program MicroMockers Program')
    #
    # def test_create_when_conditional_offer_with_uuid_exists(self):
    #     """
    #     Verify a program offer can be created if a conditional offer with different type and same uuid already exists.
    #     """
    #     data = self.generate_data()
    #     factories.ProgramOfferFactory(
    #         condition__program_uuid=data['program_uuid'],
    #         offer_type=ConditionalOffer.VOUCHER,
    #     )
    #     form = ProgramOfferForm(request=self.request, data=data)
    #     self.assertTrue(form.is_valid())
