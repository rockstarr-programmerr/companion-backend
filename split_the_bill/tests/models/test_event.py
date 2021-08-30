from model_bakery import baker
from faker import Faker
from django.test import TestCase

from split_the_bill.models import Event, Fund

fake = Faker()


class EventModelTestCase(TestCase):
    def test__fund_created__after__creating_event(self):
        event = baker.make(Event)
        self.assertTrue(Fund.objects.filter(event=event).exists())

    def test__fund_not_created_again__after__updating_event(self):
        event = baker.make(Event)
        fund = event.fund
        fund.balance = 100
        fund.save()

        event.name = fake.text(max_nb_chars=10)
        event.save()
        event.refresh_from_db()

        new_fund = event.fund
        self.assertEqual(new_fund.pk, fund.pk)
        self.assertEqual(new_fund.balance, 100)
