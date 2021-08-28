import json
from model_bakery import baker
from faker import Faker
from freezegun import freeze_time
from parameterized import parameterized


from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from split_the_bill.models import Trip

fake = Faker()
User = get_user_model()
default_time = '2021-08-23T08:13:16.276029Z'


class TripViewSetTestCase(APITestCase):
    url = '/split-the-bill/trips/'
    trip1_create_time = '2021-08-21T08:13:16.276029Z'
    trip2_create_time = '2021-08-22T08:13:16.276029Z'

    def setUp(self):
        super().setUp()
        self.creator = baker.make(User)
        self.members = baker.make(User, _quantity=4)

        with freeze_time(self.trip1_create_time):
            self.trip1 = baker.make(Trip, creator=self.creator)
            self.trip1.members.add(self.creator, *self.members[:2])

        with freeze_time(self.trip2_create_time):
            self.trip2 = baker.make(Trip, creator=self.creator)
            self.trip2.members.add(self.creator, *self.members[2:])

    @property
    def trip1_json(self):
        return {
            "pk": self.trip1.pk,
            "name": self.trip1.name,
            "creator": self.get_user_json(self.creator),
            "members": [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            "create_time": self.trip1_create_time
        }

    @property
    def trip2_json(self):
        return {
            "pk": self.trip2.pk,
            "name": self.trip2.name,
            "creator": self.get_user_json(self.creator),
            "members": [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[2]),
                self.get_user_json(self.members[3]),
            ],
            "create_time": self.trip2_create_time
        }

    @staticmethod
    def get_user_json(user):
        return {
            'pk': user.pk,
            'username': user.username,
            'email': user.email,
        }

    def test__get_list(self):
        self.client.force_authenticate(user=self.creator)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps([
            self.trip1_json,
            self.trip2_json,
        ])

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        [1],
        [2],
    ])
    def test__get_detail(self, trip_number):
        self.client.force_authenticate(user=self.creator)

        pk = getattr(self, f'trip{trip_number}').pk
        res = self.client.get(f'{self.url}{pk}/')
        self.assertEqual(res.status_code, 200)

        actual = res.json()

        expected_data = getattr(self, f'trip{trip_number}_json')
        expected = json.dumps(expected_data)

        self.assertJSONEqual(expected, actual)

    @freeze_time(default_time)
    def test__post(self):
        trip_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        self.client.force_authenticate(user=user)

        res = self.client.post(self.url, {'name': trip_name})
        self.assertEqual(res.status_code, 201)

        # Check response
        actual = res.json()
        self.assertIn('pk', actual.keys())
        actual.pop('pk')

        expected_data = json.dumps({
            'name': trip_name,
            'creator': self.get_user_json(user),
            'members': [
                self.get_user_json(user),
            ],
            'create_time': default_time
        })

        self.assertJSONEqual(expected_data, actual)

        # Check DB
        trip = Trip.objects.filter(name=trip_name).first()
        self.assertIsNotNone(trip)
        self.assertEqual(trip.name, trip_name)
        self.assertEqual(trip.creator, user)

        members = trip.members.all()
        self.assertEqual(len(members), 1)
        self.assertIn(user, members)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch(self, method):
        self.client.force_authenticate(user=self.creator)
        trip_name = fake.text(max_nb_chars=150)

        url = f'{self.url}{self.trip1.pk}/'
        req_method = getattr(self.client, method)
        res = req_method(url, {'name': trip_name})
        self.assertEqual(res.status_code, 200)

        # Check response
        actual = res.json()
        self.assertIn('pk', actual.keys())
        actual.pop('pk')

        expected_data = json.dumps({
            'name': trip_name,
            'creator': self.get_user_json(self.creator),
            'members': [
                self.get_user_json(self.creator),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            'create_time': self.trip1_create_time
        })

        self.assertJSONEqual(expected_data, actual)

        # Check DB
        trip = Trip.objects.filter(name=trip_name).first()
        self.assertIsNotNone(trip)
        self.assertEqual(trip.name, trip_name)
        self.assertEqual(trip.creator, self.creator)

        members = trip.members.all()
        self.assertEqual(len(members), 3)
        self.assertIn(self.creator, members)

    def test__delete(self):
        self.client.force_authenticate(user=self.creator)

        url = f'{self.url}{self.trip1.pk}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Trip.objects.filter(pk=self.trip1.pk).exists())

    def test__get_list_permission(self):
        user = baker.make(User)
        trip3 = baker.make(Trip, creator=user)
        trip3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)
        data = res.json()

        self.assertEqual(len(data), 1)
        pks = [trip['pk'] for trip in data]
        self.assertNotIn(self.trip1.pk, pks)
        self.assertNotIn(self.trip2.pk, pks)
        self.assertIn(trip3.pk, pks)

    def test__get_detail_permission(self):
        user = baker.make(User)
        trip3 = baker.make(Trip, creator=user)
        trip3.members.add(user)

        trip3_url = f'{self.url}{trip3.pk}/'
        self.client.force_authenticate(user=user)
        res = self.client.get(trip3_url)
        self.assertEqual(res.status_code, 200)

        for index, member in enumerate(self.members):
            self.client.force_authenticate(user=member)
            res = self.client.get(trip3_url)
            self.assertEqual(res.status_code, 404)

            res1 = self.client.get(f'{self.url}{self.trip1.pk}/')
            res2 = self.client.get(f'{self.url}{self.trip2.pk}/')
            if index in [0, 1]:
                self.assertEqual(res1.status_code, 200)
                self.assertEqual(res2.status_code, 404)
            else:
                self.assertEqual(res1.status_code, 404)
                self.assertEqual(res2.status_code, 200)

        for trip in [self.trip1, self.trip2]:
            self.client.force_authenticate(user=user)
            res = self.client.get(f'{self.url}{trip.pk}/')
            self.assertEqual(res.status_code, 404)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch_permission(self, method):
        trip_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        trip3 = baker.make(Trip, creator=user)
        trip3.members.add(user)

        self.client.force_authenticate(user=user)
        req_method = getattr(self.client, method)
        res = req_method(f'{self.url}{trip3.pk}/', {'name': trip_name})
        self.assertEqual(res.status_code, 200)

        for trip in [self.trip1, self.trip2]:
            res = req_method(f'{self.url}{trip.pk}/', {'name': trip_name})
            self.assertEqual(res.status_code, 404)

        for index, member in enumerate(self.members):
            self.client.force_authenticate(user=member)
            res1 = req_method(f'{self.url}{self.trip1.pk}/', {'name': trip_name})
            res2 = req_method(f'{self.url}{self.trip2.pk}/', {'name': trip_name})

            if index in [0, 1]:
                self.assertEqual(res1.status_code, 403)
                self.assertEqual(res2.status_code, 404)
            else:
                self.assertEqual(res1.status_code, 404)
                self.assertEqual(res2.status_code, 403)

    def test__delete_permission(self):
        user = baker.make(User)
        trip3 = baker.make(Trip, creator=user)
        trip3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.delete(f'{self.url}{trip3.pk}/')
        self.assertEqual(res.status_code, 204)

        for trip in [self.trip1, self.trip2]:
            res = self.client.delete(f'{self.url}{trip.pk}/')
            self.assertEqual(res.status_code, 404)

        for member in self.trip1.members.all():
            if self.trip1.is_creator(member):
                continue

            self.client.force_authenticate(user=member)
            res = self.client.delete(f'{self.url}{self.trip1.pk}/')
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
        self.client.patch(f'{self.url}{self.trip1.pk}/', data)

        self.trip1.refresh_from_db()
        self.assertEqual(self.trip1.name, name)
        self.assertEqual(self.trip1.creator, self.creator)
        self.assertNotEqual(self.trip1.creator, user)
