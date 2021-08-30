import json
from model_bakery import baker
from faker import Faker
from freezegun import freeze_time
from parameterized import parameterized


from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from split_the_bill.models import Event

fake = Faker()
User = get_user_model()
default_time = '2021-08-23T08:13:16.276029Z'


class EventViewSetTestCase(APITestCase):
    url = '/split-the-bill/events/'
    event1_create_time = '2021-08-21T08:13:16.276029Z'
    event2_create_time = '2021-08-22T08:13:16.276029Z'

    def setUp(self):
        super().setUp()
        self.creator = baker.make(User)
        self.members = baker.make(User, _quantity=4)

        with freeze_time(self.event1_create_time):
            self.event1 = baker.make(Event, creator=self.creator)
            self.event1.members.add(self.creator, *self.members[:2])

        with freeze_time(self.event2_create_time):
            self.event2 = baker.make(Event, creator=self.creator)
            self.event2.members.add(self.creator, *self.members[2:])

    def get_event1_json(self, request):
        pk = self.event1.pk
        return {
            "url": reverse('event-detail', kwargs={'pk': pk}, request=request),
            "pk": pk,
            "name": self.event1.name,
            "creator": self.get_user_json(self.creator),
            "members": [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            "create_time": self.event1_create_time
        }

    def get_event2_json(self, request):
        pk = self.event2.pk
        return {
            "url": reverse('event-detail', kwargs={'pk': pk}, request=request),
            "pk": pk,
            "name": self.event2.name,
            "creator": self.get_user_json(self.creator),
            "members": [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[2]),
                self.get_user_json(self.members[3]),
            ],
            "create_time": self.event2_create_time
        }

    @staticmethod
    def get_user_json(user):
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
        return f'{self.url}{pk}/add-members/'

    def get_remove_members_url(self, pk):
        return f'{self.url}{pk}/remove-members/'

    def test__get_list(self):
        self.client.force_authenticate(user=self.creator)
        res = self.client.get(self.url)
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
        res = self.client.get(f'{self.url}{pk}/')
        self.assertEqual(res.status_code, 200)

        actual = res.json()

        expected_data = getattr(self, f'get_event{event_number}_json')(res.wsgi_request)
        expected = json.dumps(expected_data)

        self.assertJSONEqual(expected, actual)

    @freeze_time(default_time)
    def test__post(self):
        event_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        self.client.force_authenticate(user=user)

        res = self.client.post(self.url, {'name': event_name})
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
            'create_time': default_time
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

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch(self, method):
        self.client.force_authenticate(user=self.creator)
        event_name = fake.text(max_nb_chars=150)

        url = f'{self.url}{self.event1.pk}/'
        req_method = getattr(self.client, method)
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
            'create_time': self.event1_create_time
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

    def test__delete(self):
        self.client.force_authenticate(user=self.creator)

        url = f'{self.url}{self.event1.pk}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Event.objects.filter(pk=self.event1.pk).exists())

    def test__get_list_permission(self):
        user = baker.make(User)
        event3 = baker.make(Event, creator=user)
        event3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)
        data = res.json()
        results = data['results']

        self.assertEqual(len(results), 1)
        pks = [event['pk'] for event in results]
        self.assertNotIn(self.event1.pk, pks)
        self.assertNotIn(self.event2.pk, pks)
        self.assertIn(event3.pk, pks)

    def test__get_detail_permission(self):
        user = baker.make(User)
        event3 = baker.make(Event, creator=user)
        event3.members.add(user)

        event3_url = f'{self.url}{event3.pk}/'
        self.client.force_authenticate(user=user)
        res = self.client.get(event3_url)
        self.assertEqual(res.status_code, 200)

        for index, member in enumerate(self.members):
            self.client.force_authenticate(user=member)
            res = self.client.get(event3_url)
            self.assertEqual(res.status_code, 404)

            res1 = self.client.get(f'{self.url}{self.event1.pk}/')
            res2 = self.client.get(f'{self.url}{self.event2.pk}/')
            if index in [0, 1]:
                self.assertEqual(res1.status_code, 200)
                self.assertEqual(res2.status_code, 404)
            else:
                self.assertEqual(res1.status_code, 404)
                self.assertEqual(res2.status_code, 200)

        for event in [self.event1, self.event2]:
            self.client.force_authenticate(user=user)
            res = self.client.get(f'{self.url}{event.pk}/')
            self.assertEqual(res.status_code, 404)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch_permission(self, method):
        event_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        event3 = baker.make(Event, creator=user)
        event3.members.add(user)

        self.client.force_authenticate(user=user)
        req_method = getattr(self.client, method)
        res = req_method(f'{self.url}{event3.pk}/', {'name': event_name})
        self.assertEqual(res.status_code, 200)

        for event in [self.event1, self.event2]:
            res = req_method(f'{self.url}{event.pk}/', {'name': event_name})
            self.assertEqual(res.status_code, 404)

        for index, member in enumerate(self.members):
            self.client.force_authenticate(user=member)
            res1 = req_method(f'{self.url}{self.event1.pk}/', {'name': event_name})
            res2 = req_method(f'{self.url}{self.event2.pk}/', {'name': event_name})

            if index in [0, 1]:
                self.assertEqual(res1.status_code, 403)
                self.assertEqual(res2.status_code, 404)
            else:
                self.assertEqual(res1.status_code, 404)
                self.assertEqual(res2.status_code, 403)

    def test__delete_permission(self):
        user = baker.make(User)
        event3 = baker.make(Event, creator=user)
        event3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.delete(f'{self.url}{event3.pk}/')
        self.assertEqual(res.status_code, 204)

        for event in [self.event1, self.event2]:
            res = self.client.delete(f'{self.url}{event.pk}/')
            self.assertEqual(res.status_code, 404)

        for member in self.event1.members.all():
            if self.event1.is_creator(member):
                continue

            self.client.force_authenticate(user=member)
            res = self.client.delete(f'{self.url}{self.event1.pk}/')
            self.assertEqual(res.status_code, 403)

    @parameterized.expand([
        ['get', url],
        ['get', url + '1/'],
        ['post', url + '1/'],
        ['put', url + '1/'],
        ['patch', url + '1/'],
        ['delete', url + '1/'],
    ])
    def test__unauthenticated_user_cannot_access(self, method, url):
        self.client.force_authenticate(user=None)
        req_method = getattr(self.client, method)
        res = req_method(url)
        self.assertEqual(res.status_code, 401)

    def test__cannot_update_creator(self):
        self.client.force_authenticate(user=self.creator)
        user = baker.make(User)

        name = fake.text(max_nb_chars=150)
        data = {
            'name': name,
            'creator': user.pk
        }
        self.client.patch(f'{self.url}{self.event1.pk}/', data)

        self.event1.refresh_from_db()
        self.assertEqual(self.event1.name, name)
        self.assertEqual(self.event1.creator, self.creator)
        self.assertNotEqual(self.event1.creator, user)

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
