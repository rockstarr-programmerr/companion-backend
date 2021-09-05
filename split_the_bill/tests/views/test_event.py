import json

from django.contrib.auth import get_user_model
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker
from parameterized import parameterized
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from split_the_bill.models import Event
from split_the_bill.utils.datetime import format_iso
from companion.utils.url import update_url_params
from split_the_bill.views import EventViewSet

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
        return self.get_event_json(self.event1, request)

    def get_event2_json(self, request):
        return self.get_event_json(self.event2, request)

    def get_event_json(self, event, request):
        members = event.members.all()
        transactions_url = reverse('transaction-list', request=request)
        transactions_url = update_url_params(transactions_url, {'event': event.pk})
        return {
            'url': reverse('event-detail', kwargs={'pk': event.pk}, request=request),
            'pk': event.pk,
            'name': event.name,
            'creator': self.get_user_json(event.creator, request=request),
            'members': [
                self.get_user_json(member, request=request)
                for member in members
            ],
            'create_time': format_iso(event.create_time),
            'transactions_url': transactions_url,
            'extra_action_urls': {
                'add_members': reverse('event-add-members', kwargs={'pk': event.pk}, request=request),
                'remove_members': reverse('event-remove-members', kwargs={'pk': event.pk}, request=request),
            },
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
            self.get_event2_json(res.wsgi_request),
            self.get_event1_json(res.wsgi_request),
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

    def test__filters_and_ordering(self):
        self.assertListEqual(EventViewSet.ordering_fields, ['name', 'create_time', 'update_time'])
        self.assertListEqual(EventViewSet.ordering, ['-create_time'])


class EventCreateTestCase(_EventViewSetTestCase):
    @freeze_time(DEFAULT_TIME)
    def test__post(self):
        event_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        self.client.force_authenticate(user=user)

        res = self.client.post(URL, {'name': event_name})
        self.assertEqual(res.status_code, 201)

        # Check DB
        event = Event.objects.filter(name=event_name).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.creator, user)

        members = event.members.all()
        self.assertEqual(len(members), 1)
        self.assertIn(user, members)

        # Check response
        actual = res.json()
        expected_data = json.dumps(
            self.get_event_json(event, res.wsgi_request)
        )

        self.assertJSONEqual(expected_data, actual)

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

        # Check DB
        event = Event.objects.filter(name=event_name).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.name, event_name)
        self.assertEqual(event.creator, self.creator)

        members = event.members.all()
        self.assertEqual(len(members), 3)
        self.assertIn(self.creator, members)

        # Check response
        actual = res.json()
        expected_data = json.dumps(
            self.get_event_json(event, res.wsgi_request)
        )

        self.assertJSONEqual(expected_data, actual)

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
            'member_usernames': [member.username for member in new_members]
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
        ['add', 'member_usernames'],
        ['remove', 'member_pks'],
    ])
    def test__add_or_remove_members_validations(self, action, param_key):
        self.client.force_authenticate(user=self.creator)
        url = getattr(self, f'get_{action}_members_url')(self.event1.pk)

        # param_key is empty
        data = {param_key: []}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {param_key: ['This list may not be empty.']})

        # More than 100 param_key
        data = {param_key: list(range(1, 102))}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {param_key: ['Ensure this field has no more than 100 elements.']})

        if action == 'remove':
            # member_pk < 1
            data = {param_key: [1, 2, 3, -1]}
            res = self.client.post(url, data)
            self.assertEqual(res.status_code, 400)
            self.assertDictEqual(res.json(), {param_key: {'3': ['Ensure this value is greater than or equal to 1.']}})

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
        data = {'member_usernames': [new_user.username]}

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
