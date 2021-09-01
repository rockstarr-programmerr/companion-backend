import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker
from parameterized import parameterized
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from split_the_bill.models import Event, Transaction

fake = Faker()
User = get_user_model()

URL = '/split-the-bill/events/'
EVENT1_CREATE_TIME = '2021-08-21T08:13:16.276029Z'
EVENT2_CREATE_TIME = '2021-08-22T08:13:16.276029Z'
DEFAULT_TIME = '2021-08-23T08:13:16.276029Z'


class _EventViewSetTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.creator = baker.make(User)
        self.members = baker.make(User, _quantity=4)

        with freeze_time(EVENT1_CREATE_TIME):
            self.event1 = baker.make(Event, creator=self.creator)
            self.event1.members.add(self.creator, *self.members[:2])

        with freeze_time(EVENT2_CREATE_TIME):
            self.event2 = baker.make(Event, creator=self.creator)
            self.event2.members.add(self.creator, *self.members[2:])

    def get_event1_json(self, request):
        pk = self.event1.pk
        return {
            'url': reverse('event-detail', kwargs={'pk': pk}, request=request),
            'pk': pk,
            'name': self.event1.name,
            'creator': self.get_user_json(self.creator),
            'members': [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            'create_time': EVENT1_CREATE_TIME
        }

    def get_event2_json(self, request):
        pk = self.event2.pk
        return {
            'url': reverse('event-detail', kwargs={'pk': pk}, request=request),
            'pk': pk,
            'name': self.event2.name,
            'creator': self.get_user_json(self.creator),
            'members': [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[2]),
                self.get_user_json(self.members[3]),
            ],
            'create_time': EVENT2_CREATE_TIME
        }

    @staticmethod
    def get_user_json(user_or_pk):
        if not user_or_pk:
            return None
        elif isinstance(user_or_pk, int):
            user = User.objects.get(pk=user_or_pk)
        else:
            user = user_or_pk

        return {
            'pk': user.pk,
            'username': user.username,
            'email': user.email,
        }

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

    def get_add_members_url(self, pk):
        return f'{URL}{pk}/add-members/'

    def get_remove_members_url(self, pk):
        return f'{URL}{pk}/remove-members/'


class EventReadTestCase(_EventViewSetTestCase):
    def test__get_list(self):
        self.client.force_authenticate(user=self.creator)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        results = [
            self.get_event1_json(res.wsgi_request),
            self.get_event2_json(res.wsgi_request),
        ]
        expected = json.dumps(self.get_pagination_json(results))

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        [1],
        [2],
    ])
    def test__get_detail(self, event_number):
        self.client.force_authenticate(user=self.creator)

        pk = getattr(self, f'event{event_number}').pk
        res = self.client.get(f'{URL}{pk}/')
        self.assertEqual(res.status_code, 200)

        actual = res.json()

        expected_data = getattr(self, f'get_event{event_number}_json')(res.wsgi_request)
        expected = json.dumps(expected_data)

        self.assertJSONEqual(expected, actual)

    def test__get_list_permission(self):
        """
        Creator and member can only see list of their events
        """
        creator = baker.make(User)
        member = baker.make(User)
        event3 = baker.make(Event, creator=creator)
        event3.members.add(creator, member)

        for user in [creator, member]:
            self.client.force_authenticate(user=user)
            res = self.client.get(URL)
            data = res.json()
            results = data['results']

            self.assertEqual(len(results), 1)
            pks = [event['pk'] for event in results]
            self.assertNotIn(self.event1.pk, pks)
            self.assertNotIn(self.event2.pk, pks)
            self.assertIn(event3.pk, pks)

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, 401)

    def test__get_detail_permission(self):
        """
        Creator and member can only see detail of their events
        """
        creator = baker.make(User)
        member = baker.make(User)
        event3 = baker.make(Event, creator=creator)
        event3.members.add(creator, member)
        event3_url = f'{URL}{event3.pk}/'

        for user in [creator, member]:
            self.client.force_authenticate(user=user)
            res = self.client.get(event3_url)
            self.assertEqual(res.status_code, 200)

            for event in [self.event1, self.event2]:
                res = self.client.get(f'{URL}{event.pk}/')
                self.assertEqual(res.status_code, 404)

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(event3_url)
        self.assertEqual(res.status_code, 401)


class EventCreateTestCase(_EventViewSetTestCase):
    @freeze_time(DEFAULT_TIME)
    def test__post(self):
        event_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        self.client.force_authenticate(user=user)

        res = self.client.post(URL, {'name': event_name})
        self.assertEqual(res.status_code, 201)

        # Check response
        actual = res.json()
        self.assertIn('pk', actual.keys())
        pk = actual.pop('pk')

        expected_data = json.dumps({
            'url': reverse('event-detail', kwargs={'pk': pk}, request=res.wsgi_request),
            'name': event_name,
            'creator': self.get_user_json(user),
            'members': [
                self.get_user_json(user),
            ],
            'create_time': DEFAULT_TIME
        })

        self.assertJSONEqual(expected_data, actual)

        # Check DB
        event = Event.objects.filter(name=event_name).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.creator, user)

        members = event.members.all()
        self.assertEqual(len(members), 1)
        self.assertIn(user, members)

    def test__post_permission(self):
        """
        Only authenticated user can create event
        """
        event_name = fake.text(max_nb_chars=150)
        user = baker.make(User)

        res = self.client.post(URL, {'name': event_name})
        self.assertEqual(res.status_code, 401)
        self.assertFalse(Event.objects.filter(name=event_name).exists())

        self.client.force_authenticate(user=user)
        res = self.client.post(URL, {'name': event_name})
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Event.objects.filter(name=event_name).exists())


class EventUpdateTestCase(_EventViewSetTestCase):
    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch(self, method):
        event_name = fake.text(max_nb_chars=150)

        url = f'{URL}{self.event1.pk}/'
        req_method = getattr(self.client, method)

        self.client.force_authenticate(user=self.creator)
        res = req_method(url, {'name': event_name})
        self.assertEqual(res.status_code, 200)

        # Check response
        actual = res.json()
        self.assertIn('pk', actual.keys())
        pk = actual.pop('pk')

        expected_data = json.dumps({
            'url': reverse('event-detail', kwargs={'pk': pk}, request=res.wsgi_request),
            'name': event_name,
            'creator': self.get_user_json(self.creator),
            'members': [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            'create_time': EVENT1_CREATE_TIME
        })

        self.assertJSONEqual(expected_data, actual)

        # Check DB
        event = Event.objects.filter(name=event_name).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.creator, self.creator)

        members = event.members.all()
        self.assertEqual(len(members), 3)
        self.assertIn(self.creator, members)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__cannot_update_creator(self, method):
        self.client.force_authenticate(user=self.creator)
        user = baker.make(User)

        name = fake.text(max_nb_chars=150)
        data = {
            'name': name,
            'creator': user.pk
        }
        req_method = getattr(self.client, method)
        req_method(f'{URL}{self.event1.pk}/', data)

        self.event1.refresh_from_db()
        self.assertEqual(self.event1.name, name)
        self.assertEqual(self.event1.creator, self.creator)
        self.assertNotEqual(self.event1.creator, user)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch_permission(self, method):
        """
        Only creator can update their event
        """
        event_name = fake.text(max_nb_chars=150)
        creator = baker.make(User)
        member = baker.make(User)
        event3 = baker.make(Event, creator=creator)
        event3.members.add(creator, member)
        req_method = getattr(self.client, method)

        # Unauthenticated user cannot access
        res = req_method(f'{URL}{event3.pk}/', {'name': event_name})
        self.assertEqual(res.status_code, 401)
        event3.refresh_from_db()
        self.assertNotEqual(event3.name, event_name)

        # Member cannot update event
        self.client.force_authenticate(user=member)
        req_method = getattr(self.client, method)
        res = req_method(f'{URL}{event3.pk}/', {'name': event_name})
        self.assertEqual(res.status_code, 403)
        event3.refresh_from_db()
        self.assertNotEqual(event3.name, event_name)

        # Cannot update other events
        for user in [creator, member]:
            self.client.force_authenticate(user=user)
            for event in [self.event1, self.event2]:
                res = req_method(f'{URL}{event.pk}/', {'name': event_name})
                self.assertEqual(res.status_code, 404)
                event.refresh_from_db()
                self.assertNotEqual(event.name, event_name)

        # Creator can update
        self.client.force_authenticate(user=creator)
        res = req_method(f'{URL}{event3.pk}/', {'name': event_name})
        self.assertEqual(res.status_code, 200)
        event3.refresh_from_db()
        self.assertEqual(event3.name, event_name)


class EventDeleteTestCase(_EventViewSetTestCase):
    def test__delete(self):
        self.client.force_authenticate(user=self.creator)

        url = f'{URL}{self.event1.pk}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Event.objects.filter(pk=self.event1.pk).exists())

    def test__delete_permission(self):
        """
        Only creator can delete event
        """
        creator = baker.make(User)
        member = baker.make(User)
        event3 = baker.make(Event, creator=creator)
        event3.members.add(creator, member)

        # Unauthenticated user cannot access
        res = self.client.delete(f'{URL}{event3.pk}/')
        self.assertEqual(res.status_code, 401)
        self.assertTrue(Event.objects.filter(pk=event3.pk).exists())

        # Member cannot delete event
        self.client.force_authenticate(user=member)
        res = self.client.delete(f'{URL}{event3.pk}/')
        self.assertEqual(res.status_code, 403)
        self.assertTrue(Event.objects.filter(pk=event3.pk).exists())

        # Cannot delete other events
        for user in [creator, member]:
            self.client.force_authenticate(user=user)
            for event in [self.event1, self.event2]:
                res = self.client.delete(f'{URL}{event.pk}/')
                self.assertEqual(res.status_code, 404)
                self.assertTrue(Event.objects.filter(pk=event.pk).exists())

        # Creator can delete event
        self.client.force_authenticate(user=creator)
        res = self.client.delete(f'{URL}{event3.pk}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Event.objects.filter(pk=event3.pk).exists())


class EventAddRemoveMembersTestCase(_EventViewSetTestCase):
    def test__add_members(self):
        self.client.force_authenticate(user=self.creator)

        new_members = baker.make(User, _quantity=3)
        existing_members = self.event1.members.all()
        for member in new_members:
            self.assertNotIn(member, existing_members)

        url = self.get_add_members_url(self.event1.pk)
        data = {
            'member_pks': [member.pk for member in new_members]
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)

        self.event1.refresh_from_db()
        members = self.event1.members.all()
        for member in new_members:
            self.assertIn(member, members)

    def test__remove_members(self):
        self.client.force_authenticate(user=self.creator)

        new_members = baker.make(User, _quantity=3)
        self.event1.members.add(*new_members)
        members = self.event1.members.all()

        for member in new_members:
            self.assertIn(member, members)

        url = self.get_remove_members_url(self.event1.pk)
        data = {
            'member_pks': [member.pk for member in new_members]
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)

        self.event1.refresh_from_db()
        members = self.event1.members.all()
        for member in new_members:
            self.assertNotIn(member, members)

    @parameterized.expand([
        ['add'],
        ['remove'],
    ])
    def test__add_or_remove_members_validations(self, action):
        self.client.force_authenticate(user=self.creator)
        url = getattr(self, f'get_{action}_members_url')(self.event1.pk)

        # member_pks is empty
        data = {'member_pks': []}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': ['This list may not be empty.']})

        # member_pk < 1
        data = {'member_pks': [1, 2, 3, -1]}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': {'3': ['Ensure this value is greater than or equal to 1.']}})

        # More than 100 member_pks
        data = {'member_pks': list(range(1, 102))}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': ['Ensure this field has no more than 100 elements.']})

    def test__cannot_remove_yourself_from_event(self):
        self.client.force_authenticate(user=self.creator)
        url = self.get_remove_members_url(self.event1.pk)

        data = {'member_pks': [self.creator.pk]}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': ['Cannot remove yourself from event.']})

        self.assertIn(self.creator, self.event1.members.all())

    def test__add_members__permission(self):
        """
        Only creator can add members
        """
        new_user = baker.make(User)
        url = self.get_add_members_url(self.event1.pk)
        data = {'member_pks': [new_user.pk]}

        # Unauthenticated user cannot access
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 401)
        self.assertNotIn(new_user, self.event1.members.all())

        # Member cannot add member
        member = self.event1.members.exclude(pk=self.creator.pk).first()
        self.client.force_authenticate(user=member)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 403)
        self.assertNotIn(new_user, self.event1.members.all())

        # Creator can add member
        self.client.force_authenticate(user=self.creator)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(new_user, self.event1.members.all())

    def test__remove_members__permission(self):
        url = self.get_remove_members_url(self.event1.pk)
        member = self.event1.members.exclude(pk=self.creator.pk).first()
        data = {'member_pks': [member.pk]}

        # Unauthenticated user cannot access
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 401)
        self.assertIn(member, self.event1.members.all())

        # Member cannot remove member
        other_member = self.event1.members.exclude(pk__in=[self.creator.pk, member.pk]).first()
        self.client.force_authenticate(user=other_member)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 403)
        self.assertIn(member, self.event1.members.all())

        # Creator can remove member
        self.client.force_authenticate(user=self.creator)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(member, self.event1.members.all())


class EventAddRemoveTransactionTestCase(_EventViewSetTestCase):
    CREATOR_PK = 5426432
    MEMBER_1_PK = 874437
    MEMBER_2_PK = 76493273

    def setUp(self):
        super().setUp()
        self.creator = baker.make(User, pk=self.CREATOR_PK)
        self.member_1 = baker.make(User, pk=self.MEMBER_1_PK)
        self.member_2 = baker.make(User, pk=self.MEMBER_2_PK)
        self.event = baker.make(Event, creator=self.creator)
        self.event.members.add(self.creator, self.member_1, self.member_2)

    @parameterized.expand([
        ['user_to_user', MEMBER_1_PK, MEMBER_2_PK, False, False, False],
        ['user_to_user', CREATOR_PK, MEMBER_1_PK, False, False, False],
        ['user_to_user', CREATOR_PK, MEMBER_2_PK, False, False, False],

        ['user_to_fund', CREATOR_PK, None, True, False, False],
        ['user_to_fund', MEMBER_1_PK, None, True, False, False],
        ['user_to_fund', MEMBER_2_PK, None, True, False, False],

        ['fund_to_user', None, CREATOR_PK, False, True, False],
        ['fund_to_user', None, MEMBER_1_PK, False, True, False],
        ['fund_to_user', None, MEMBER_2_PK, False, True, False],

        ['user_expense', CREATOR_PK, None, False, False, True],
        ['user_expense', MEMBER_1_PK, None, False, False, True],
        ['user_expense', MEMBER_2_PK, None, False, False, True],

        ['fund_expense', None, None, False, True, True],
    ])
    def test__add_transaction(
        self, transaction_type, from_user, to_user,
        expected_is_deposit, expected_is_withdrawal, expected_is_expense
    ):
        self.client.force_authenticate(user=self.creator)
        url = f'{URL}{self.event.pk}/add-transaction/'
        data = {
            'transaction_type': transaction_type,
            'from_user': from_user,
            'to_user': to_user,
        }
        now = timezone.now()
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)

        # Test response
        actual = res.json()
        pk = actual.get('pk')
        expected = json.dumps({
            'pk': pk,
            'transaction_type': transaction_type,
            'from_user': self.get_user_json(from_user),
            'to_user': self.get_user_json(to_user),
        })
        self.assertJSONEqual(expected, actual)

        # Test DB
        transaction = Transaction.objects.get(pk=pk)
        self.assertEqual(getattr(transaction.from_user, 'pk', None), from_user)
        self.assertEqual(getattr(transaction.to_user, 'pk', None), to_user)
        self.assertEqual(transaction.is_deposit, expected_is_deposit)
        self.assertEqual(transaction.is_withdrawal, expected_is_withdrawal)
        self.assertEqual(transaction.is_expense, expected_is_expense)
        self.assertAlmostEqual(transaction.create_time, now, delta=timedelta(seconds=5))
        self.assertAlmostEqual(transaction.update_time, now, delta=timedelta(seconds=5))

    def test__remove_transaction(self):
        transaction = baker.make(Transaction, event=self.event)

        self.client.force_authenticate(user=self.creator)
        url = f'{URL}{self.event.pk}/remove-transaction/'
        data = {'transaction_pk': transaction.pk}
        res = self.client.post(url, data)

        self.assertEqual(res.status_code, 204)
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())


class EventGetTransactionsTestCase(_EventViewSetTestCase):
    NOW = '2021-07-30T14:05:26Z'

    def setUp(self):
        self.creator = baker.make(User)
        self.member = baker.make(User)
        self.event = baker.make(Event, creator=self.creator)
        self.event.members.add(self.creator, self.member)
        self.transactions = []

        create_time = parse_datetime(self.NOW)
        for _ in range(10):
            with freeze_time(create_time):
                transaction = baker.make(Transaction, event=self.event)
                self.transactions.append(transaction)
            create_time -= timedelta(hours=1)

    def test__filter_transactions__response(self):
        self.client.force_authenticate(user=self.creator)
        url = f'{URL}{self.event.pk}/get-transactions/'

        params = {
            'start_time': '2021-07-30T14:05:26Z',
            'end_time': '2021-07-30T14:05:26Z',
        }
        res = self.client.get(url, params)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        trans = self.transactions[0]
        expected_res = [{
            'pk': trans.pk,
            'transaction_type': trans.get_transaction_type(),
            'from_user': trans.from_user,
            'to_user': trans.to_user,
            'create_time': self.NOW,
            'update_time': self.NOW,
        }]
        expected = json.dumps(self.get_pagination_json(expected_res))

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        [None, None, 1, 10],

        # With either start or end time
        ['2021-07-30T10:05:26Z', None, 1, 5],
        [None, '2021-07-30T07:05:26Z', 8, 10],

        # With both start and end time
        ['2021-07-30T10:05:26Z', '2021-07-30T14:05:26Z', 1, 5],
        ['2021-07-30T10:06:26Z', '2021-07-30T14:05:25Z', 2, 4],

        # With timezone
        ['2021-07-30T17:05:26+0700', '2021-07-30T21:05:26+0700', 1, 5],
        ['2021-07-30T22:06:26+1200', '2021-07-31T02:05:25+1200', 2, 4],
    ])
    def test__filter_transactions__start_end_time(
        self, start_time, end_time,
        expected_first_transaction, expected_last_transaction
    ):
        self.client.force_authenticate(user=self.creator)
        url = f'{URL}{self.event.pk}/get-transactions/'

        params = {}
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        res = self.client.get(url, params)
        self.assertEqual(res.status_code, 200)

        results = res.json()['results']
        pks = [result['pk'] for result in results]

        if not expected_first_transaction and not expected_last_transaction:
            self.assertEqual(len(pks), 0)
        else:
            self.assertGreater(len(pks), 0)
            first_pk = pks[0]
            last_pk = pks[-1]

            trans_pks = [trans.pk for trans in self.transactions]
            first_pk_index = trans_pks.index(first_pk)
            last_pk_index = trans_pks.index(last_pk)

            self.assertEqual(first_pk_index + 1, expected_first_transaction)
            self.assertEqual(last_pk_index + 1, expected_last_transaction)
