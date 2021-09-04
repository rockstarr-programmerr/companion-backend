import json
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker
from parameterized import parameterized
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from split_the_bill.models import Event, Transaction
from split_the_bill.utils.datetime import format_iso
from split_the_bill.views import TransactionViewSet

fake = Faker()
User = get_user_model()


class _TransactionTestCase(APITestCase):
    url = reverse('transaction-list')

    def setUp(self):
        super().setUp()
        now = timezone.now()

        self.creator1 = baker.make(User)
        self.members1 = baker.make(User, _quantity=3)
        self.event1 = baker.make(Event, creator=self.creator1)
        self.event1.members.add(self.creator1, *self.members1)

        self.creator2 = baker.make(User)
        self.members2 = baker.make(User, _quantity=3)
        self.event2 = baker.make(Event, creator=self.creator2)
        self.event2.members.add(self.creator2, *self.members2)

        self.share_members = baker.make(User, _quantity=3)
        self.event1.members.add(*self.share_members)
        self.event2.members.add(*self.share_members)

        for event in [self.event1, self.event2]:
            members = event.members.all()

            current_time = now
            with freeze_time(current_time):
                baker.make(
                    Transaction,
                    event=event,
                    transaction_type=Transaction.Types.USER_TO_USER,
                    from_user=random.choice(members),
                    to_user=random.choice(members),
                    amount=random.randint(1_000, 1_000_000),
                )

            current_time -= timedelta(seconds=random.randint(1, 86400))
            with freeze_time(current_time):
                baker.make(
                    Transaction,
                    event=event,
                    transaction_type=Transaction.Types.USER_TO_FUND,
                    from_user=random.choice(members),
                    to_user=None,
                    amount=random.randint(1_000, 1_000_000),
                )

            current_time -= timedelta(seconds=random.randint(1, 86400))
            with freeze_time(current_time):
                baker.make(
                    Transaction,
                    event=event,
                    transaction_type=Transaction.Types.FUND_TO_USER,
                    from_user=None,
                    to_user=random.choice(members),
                    amount=random.randint(1_000, 1_000_000),
                )

            current_time -= timedelta(seconds=random.randint(1, 86400))
            with freeze_time(current_time):
                baker.make(
                    Transaction,
                    event=event,
                    transaction_type=Transaction.Types.USER_EXPENSE,
                    from_user=random.choice(members),
                    to_user=None,
                    amount=random.randint(1_000, 1_000_000),
                )

            current_time -= timedelta(seconds=random.randint(1, 86400))
            with freeze_time(current_time):
                baker.make(
                    Transaction,
                    event=event,
                    transaction_type=Transaction.Types.FUND_EXPENSE,
                    from_user=None,
                    to_user=None,
                    amount=random.randint(1_000, 1_000_000),
                )

    @staticmethod
    def get_detail_url(pk, request=None):
        return reverse('transaction-detail', kwargs={'pk': pk}, request=request)

    @staticmethod
    def get_event_detail_url(pk, request=None):
        return reverse('event-detail', kwargs={'pk': pk}, request=request)

    @staticmethod
    def get_user_detail_url(pk, request=None):
        return reverse('user-detail', kwargs={'pk': pk}, request=request)

    @staticmethod
    def get_pagination_json(results, count=None, next=None, previous=None):
        if count is None:
            count = len(results)

        return {
            'count': count,
            'next': next,
            'previous': previous,
            'results': results,
        }

    @staticmethod
    def get_user_json(user_or_pk, request=None):
        if not user_or_pk:
            return None
        elif isinstance(user_or_pk, int):
            user = User.objects.get(pk=user_or_pk)
        else:
            user = user_or_pk

        return {
            'url': reverse('user-detail', kwargs={'pk': user.pk}, request=request),
            'pk': user.pk,
            'username': user.username,
            'email': user.email,
            'avatar': user.avatar.path if user.avatar else None,
        }

    def get_transaction_json(self, transaction, request):
        return {
            'url': self.get_detail_url(transaction.pk, request=request),
            'pk': transaction.pk,
            'event': reverse('event-detail', kwargs={'pk': transaction.event.pk}, request=request),
            'transaction_type': transaction.transaction_type,
            'from_user': self.get_user_json(transaction.from_user, request=request) if transaction.from_user else None,
            'to_user': self.get_user_json(transaction.to_user, request=request) if transaction.to_user else None,
            'amount': transaction.amount,
            'create_time': format_iso(transaction.create_time),
            'update_time': format_iso(transaction.update_time),
        }


class TransactionReadTestCase(_TransactionTestCase):
    @parameterized.expand([
        [1, False],
        [2, False],
        [1, True],
        [2, True],
    ])
    def test__get_list(self, event_number, is_share_member):
        if is_share_member:
            members = self.share_members
            transactions = Transaction.objects.filter(event__in=[self.event1, self.event2])
        else:
            event = getattr(self, f'event{event_number}')
            members = event.members.exclude(pk__in=[member.pk for member in self.share_members])
            transactions = event.transactions.all()

        transactions = transactions.order_by('-create_time')

        user = random.choice(members)
        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps(self.get_pagination_json([
            self.get_transaction_json(transaction, res.wsgi_request)
            for transaction in transactions
        ]))

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        [1, Transaction.Types.USER_TO_USER],
        [1, Transaction.Types.USER_TO_FUND],
        [1, Transaction.Types.FUND_TO_USER],
        [1, Transaction.Types.USER_EXPENSE],
        [1, Transaction.Types.FUND_EXPENSE],
        [2, Transaction.Types.USER_TO_USER],
        [2, Transaction.Types.USER_TO_FUND],
        [2, Transaction.Types.FUND_TO_USER],
        [2, Transaction.Types.USER_EXPENSE],
        [2, Transaction.Types.FUND_EXPENSE],
    ])
    def test__get_detail(self, event_number, transaction_type):
        event = getattr(self, f'event{event_number}')
        members = event.members.all()
        user = random.choice(members)
        transaction = event.transactions.filter(transaction_type=transaction_type).first()
        url = self.get_detail_url(transaction.pk)

        self.client.force_authenticate(user=user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps(
            self.get_transaction_json(transaction, request=res.wsgi_request)
        )

        self.assertJSONEqual(expected, actual)

    def test__get_list_permission(self):
        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

        # Member of 1 event can see all transactions of that event,
        # but cannot see transactions of another event
        user = random.choice(self.event1.members.exclude(pk__in=[member.pk for member in self.share_members]))
        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)
        pks = [trans['pk'] for trans in res.json()['results']]

        this_pks = self.event1.transactions.all().values_list('pk', flat=True)
        other_pks = self.event2.transactions.all().values_list('pk', flat=True)
        for this_pk in this_pks:
            self.assertIn(this_pk, pks)
        for other_pk in other_pks:
            self.assertNotIn(other_pk, pks)

    def test__get_detail_permission(self):
        transaction = random.choice(self.event1.transactions.all())
        url = self.get_detail_url(transaction.pk)

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 401)

        # Members cannot see transactions of events they don't participate
        user = random.choice(self.event2.members.exclude(pk__in=[member.pk for member in self.share_members]))
        self.client.force_authenticate(user=user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

        # Members can see transactions of events they participate
        user = random.choice(self.share_members)
        self.client.force_authenticate(user=user)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test__filters_and_ordering(self):
        self.assertListEqual(TransactionViewSet.ordering_fields, ['amount', 'create_time', 'update_time'])
        self.assertListEqual(TransactionViewSet.ordering, ['-create_time'])


class TransactionValidationTestCase(_TransactionTestCase):
    @parameterized.expand([
        ['post'],
        ['put'],
        ['patch'],
    ])
    def test__validate__from_to_users_are_different(self, method):
        req_method = getattr(self.client, method)
        if method == 'post':
            url = self.url
        else:
            transaction = random.choice(self.event1.transactions.all())
            url = self.get_detail_url(transaction.pk)

        user = random.choice(self.event1.members.all())
        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': Transaction.Types.USER_TO_USER,
            'from_user': self.get_user_detail_url(user.pk),
            'to_user': self.get_user_detail_url(user.pk),
            'amount': random.randint(1_000, 1_000_000),
        }
        self.client.force_authenticate(user=user)
        res = req_method(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'non_field_errors': ['`from_user` and `to_user` must be different.']})

    @parameterized.expand([
        ['post'],
        ['put'],
        ['patch'],
    ])
    def test__validate__user_is_event_member(self, method):
        req_method = getattr(self.client, method)
        if method == 'post':
            url = self.url
        else:
            transaction = random.choice(self.event1.transactions.all())
            url = self.get_detail_url(transaction.pk)

        from_user = random.choice(self.event1.members.all())
        to_user = random.choice(self.event2.members.exclude(pk__in=[member.pk for member in self.share_members]))
        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': Transaction.Types.USER_TO_USER,
            'from_user': self.get_user_detail_url(from_user.pk),
            'to_user': self.get_user_detail_url(to_user.pk),
            'amount': random.randint(1_000, 1_000_000),
        }
        self.client.force_authenticate(user=self.creator1)
        res = req_method(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'non_field_errors': ["`from_user` and `to_user` must be one of event's members."]})

    @parameterized.expand([
        ['post', Transaction.Types.USER_TO_USER, True, False, 'If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.'],
        ['post', Transaction.Types.USER_TO_USER, False, True, 'If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.'],
        ['post', Transaction.Types.USER_TO_FUND, False, False, 'If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.'],
        ['post', Transaction.Types.USER_TO_FUND, False, True, 'If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.'],
        ['post', Transaction.Types.FUND_TO_USER, False, False, 'If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.'],
        ['post', Transaction.Types.FUND_TO_USER, True, False, 'If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.'],
        ['post', Transaction.Types.USER_EXPENSE, False, False, 'If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.'],
        ['post', Transaction.Types.USER_EXPENSE, False, True, 'If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.'],
        ['post', Transaction.Types.FUND_EXPENSE, True, True, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
        ['post', Transaction.Types.FUND_EXPENSE, False, True, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
        ['post', Transaction.Types.FUND_EXPENSE, True, False, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],

        ['put', Transaction.Types.USER_TO_USER, True, False, 'If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.'],
        ['put', Transaction.Types.USER_TO_USER, False, True, 'If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.'],
        ['put', Transaction.Types.USER_TO_FUND, False, False, 'If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.'],
        ['put', Transaction.Types.USER_TO_FUND, False, True, 'If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.'],
        ['put', Transaction.Types.FUND_TO_USER, False, False, 'If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.'],
        ['put', Transaction.Types.FUND_TO_USER, True, False, 'If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.'],
        ['put', Transaction.Types.USER_EXPENSE, False, False, 'If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.'],
        ['put', Transaction.Types.USER_EXPENSE, False, True, 'If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.'],
        ['put', Transaction.Types.FUND_EXPENSE, True, True, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
        ['put', Transaction.Types.FUND_EXPENSE, False, True, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
        ['put', Transaction.Types.FUND_EXPENSE, True, False, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],

        ['patch', Transaction.Types.USER_TO_USER, True, False, 'If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.'],
        ['patch', Transaction.Types.USER_TO_USER, False, True, 'If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.'],
        ['patch', Transaction.Types.USER_TO_FUND, False, False, 'If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.'],
        ['patch', Transaction.Types.USER_TO_FUND, False, True, 'If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.'],
        ['patch', Transaction.Types.FUND_TO_USER, False, False, 'If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.'],
        ['patch', Transaction.Types.FUND_TO_USER, True, False, 'If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.'],
        ['patch', Transaction.Types.USER_EXPENSE, False, False, 'If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.'],
        ['patch', Transaction.Types.USER_EXPENSE, False, True, 'If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.'],
        ['patch', Transaction.Types.FUND_EXPENSE, True, True, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
        ['patch', Transaction.Types.FUND_EXPENSE, False, True, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
        ['patch', Transaction.Types.FUND_EXPENSE, True, False, 'If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.'],
    ])
    def test__validate__transaction_logic(self, method, transaction_type, has_from_user, has_to_user, expected_msg):
        req_method = getattr(self.client, method)
        if method == 'post':
            url = self.url
        else:
            transaction = random.choice(self.event1.transactions.all())
            url = self.get_detail_url(transaction.pk)

        members = self.event1.members.all()
        self.client.force_authenticate(user=self.creator1)

        from_user = None
        to_user = None
        if has_from_user:
            from_user = random.choice(members)
        if has_to_user:
            to_user = random.choice(members)

        while from_user and to_user and from_user == to_user:
            to_user = random.choice(members)

        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': transaction_type,
            'from_user': self.get_user_detail_url(from_user.pk) if from_user else None,
            'to_user': self.get_user_detail_url(to_user.pk) if to_user else None,
            'amount': random.randint(10_000, 1_000_000),
        }

        res = req_method(url, data)
        self.assertEqual(res.status_code, 400)
        err_msg = res.json()['non_field_errors'][0]
        self.assertEqual(err_msg, expected_msg)


class TransactionCreateTestCase(_TransactionTestCase):
    @parameterized.expand([
        [Transaction.Types.USER_TO_USER, True, True],
        [Transaction.Types.USER_TO_FUND, True, False],
        [Transaction.Types.FUND_TO_USER, False, True],
        [Transaction.Types.USER_EXPENSE, True, False],
        [Transaction.Types.FUND_EXPENSE, False, False],
    ])
    def test__post(self, transaction_type, has_from_user, has_to_user):
        members = self.event1.members.all()
        user = random.choice(members)
        self.client.force_authenticate(user=user)

        from_user = None
        to_user = None
        if has_from_user:
            from_user = random.choice(members)
        if has_to_user:
            to_user = random.choice(members)

        while from_user and to_user and from_user == to_user:
            to_user = random.choice(members)

        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': transaction_type,
            'from_user': self.get_user_detail_url(from_user.pk) if from_user else None,
            'to_user': self.get_user_detail_url(to_user.pk) if to_user else None,
            'amount': random.randint(10_000, 1_000_000),
        }

        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 201)
        actual = res.json()
        pk = actual['pk']

        # Check DB
        transaction = Transaction.objects.get(pk=pk)
        self.assertEqual(transaction.event, self.event1)
        self.assertEqual(transaction.transaction_type, transaction_type)
        self.assertEqual(transaction.from_user, from_user)
        self.assertEqual(transaction.to_user, to_user)
        self.assertEqual(transaction.amount, data['amount'])
        now = timezone.now()
        self.assertAlmostEqual(transaction.create_time, now, delta=timedelta(seconds=3))
        self.assertAlmostEqual(transaction.update_time, now, delta=timedelta(seconds=3))

        # Check Response
        expected = json.dumps(
            self.get_transaction_json(transaction, res.wsgi_request)
        )
        self.assertJSONEqual(expected, actual)

    def test__post_permission(self):
        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': Transaction.Types.FUND_EXPENSE,
            'from_user': None,
            'to_user': None,
            'amount': 34658734,
        }

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 401)

        # Member of 1 event cannot create transaction for another event
        user = random.choice(self.event2.members.exclude(pk__in=[member.pk for member in self.share_members]))
        self.client.force_authenticate(user=user)
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 404)

        self.assertFalse(Transaction.objects.filter(amount=34658734).exists())

        # Members can create transaction for their event
        user = random.choice(self.event1.members.all())
        self.client.force_authenticate(user=user)
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Transaction.objects.filter(amount=34658734).exists())


class TransactionUpdateTestCase(_TransactionTestCase):
    @parameterized.expand([
        ['put', Transaction.Types.USER_TO_USER, True, True],
        ['put', Transaction.Types.USER_TO_FUND, True, False],
        ['put', Transaction.Types.FUND_TO_USER, False, True],
        ['put', Transaction.Types.USER_EXPENSE, True, False],
        ['put', Transaction.Types.FUND_EXPENSE, False, False],
        ['patch', Transaction.Types.USER_TO_USER, True, True],
        ['patch', Transaction.Types.USER_TO_FUND, True, False],
        ['patch', Transaction.Types.FUND_TO_USER, False, True],
        ['patch', Transaction.Types.USER_EXPENSE, True, False],
        ['patch', Transaction.Types.FUND_EXPENSE, False, False],
    ])
    def test__put_and_patch(self, method, transaction_type, has_from_user, has_to_user):
        transaction = random.choice(self.event1.transactions.all())
        members = self.event1.members.all()
        user = random.choice(members)
        self.client.force_authenticate(user=user)

        from_user = None
        to_user = None
        if has_from_user:
            from_user = random.choice(members)
        if has_to_user:
            to_user = random.choice(members)

        while from_user and to_user and from_user == to_user:
            to_user = random.choice(members)

        url = self.get_detail_url(transaction.pk)
        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': transaction_type,
            'from_user': self.get_user_detail_url(from_user.pk) if from_user else None,
            'to_user': self.get_user_detail_url(to_user.pk) if to_user else None,
            'amount': random.randint(10_000, 1_000_000),
        }

        req_method = getattr(self.client, method)
        res = req_method(url, data)
        actual = res.json()

        # Check DB
        instance = Transaction.objects.get(pk=transaction.pk)
        self.assertEqual(instance.event, self.event1)
        self.assertEqual(instance.transaction_type, transaction_type)
        self.assertEqual(instance.from_user, from_user)
        self.assertEqual(instance.to_user, to_user)
        self.assertEqual(instance.amount, data['amount'])
        now = timezone.now()
        self.assertAlmostEqual(instance.update_time, now, delta=timedelta(seconds=3))

        # Check Response
        expected = json.dumps(
            self.get_transaction_json(instance, res.wsgi_request)
        )
        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch__permission(self, method):
        transaction = random.choice(self.event1.transactions.all())
        url = self.get_detail_url(transaction.pk)
        req_method = getattr(self.client, method)
        data = {
            'event': self.get_event_detail_url(self.event1.pk),
            'transaction_type': Transaction.Types.FUND_EXPENSE,
            'from_user': None,
            'to_user': None,
            'amount': 9834765,
        }

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = req_method(url, data)
        self.assertEqual(res.status_code, 401)

        # Member of 1 event cannot update transaction for another event
        user = random.choice(self.event2.members.exclude(pk__in=[member.pk for member in self.share_members]))
        self.client.force_authenticate(user=user)
        res = req_method(url, data)
        self.assertEqual(res.status_code, 404)

        self.assertFalse(Transaction.objects.filter(amount=9834765).exists())

        # Members can update transaction for their event
        user = random.choice(self.event1.members.all())
        self.client.force_authenticate(user=user)
        res = req_method(url, data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Transaction.objects.filter(amount=9834765).exists())


class DeleteTransactionTestCase(_TransactionTestCase):
    def test__delete(self):
        transaction = random.choice(self.event2.transactions.all())
        user = random.choice(self.event2.members.all())
        url = self.get_detail_url(transaction.pk)

        self.client.force_authenticate(user=user)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())

    def test__delete_permission(self):
        transaction = random.choice(self.event1.transactions.all())
        user = random.choice(self.event1.members.all())
        url = self.get_detail_url(transaction.pk)

        # Unauthenticated user cannot access
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 401)

        # Member of 1 event cannot delete transaction for another event
        user = random.choice(self.event2.members.exclude(pk__in=[member.pk for member in self.share_members]))
        self.client.force_authenticate(user=user)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 404)

        self.assertTrue(Transaction.objects.filter(pk=transaction.pk).exists())

        # Members can delete transaction for their event
        user = random.choice(self.event1.members.all())
        self.client.force_authenticate(user=user)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())
