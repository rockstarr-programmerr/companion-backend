import json
from model_bakery import baker
from faker import Faker
from freezegun import freeze_time
from parameterized import parameterized


from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from split_the_bill.models import Group

fake = Faker()
User = get_user_model()
default_time = '2021-08-23T08:13:16.276029Z'


class GroupViewSetTestCase(APITestCase):
    url = '/split-the-bill/groups/'
    group1_create_time = '2021-08-21T08:13:16.276029Z'
    group2_create_time = '2021-08-22T08:13:16.276029Z'

    def setUp(self):
        super().setUp()
        self.owner = baker.make(User)
        self.members = baker.make(User, _quantity=4)

        with freeze_time(self.group1_create_time):
            self.group1 = baker.make(Group, owner=self.owner)
            self.group1.members.add(self.owner, *self.members[:2])

        with freeze_time(self.group2_create_time):
            self.group2 = baker.make(Group, owner=self.owner)
            self.group2.members.add(self.owner, *self.members[2:])

    @property
    def group1_json(self):
        return {
            "pk": self.group1.pk,
            "name": self.group1.name,
            "owner": self.get_user_json(self.owner),
            "members": [
                self.get_user_json(self.owner),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            "create_time": self.group1_create_time
        }

    @property
    def group2_json(self):
        return {
            "pk": self.group2.pk,
            "name": self.group2.name,
            "owner": self.get_user_json(self.owner),
            "members": [
                self.get_user_json(self.owner),
                self.get_user_json(self.members[2]),
                self.get_user_json(self.members[3]),
            ],
            "create_time": self.group2_create_time
        }

    @staticmethod
    def get_user_json(user):
        return {
            'pk': user.pk,
            'username': user.username,
            'email': user.email,
        }

    def test__get_list(self):
        self.client.force_authenticate(user=self.owner)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps([
            self.group1_json,
            self.group2_json,
        ])

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        [1],
        [2],
    ])
    def test__get_detail(self, group_number):
        self.client.force_authenticate(user=self.owner)

        pk = getattr(self, f'group{group_number}').pk
        res = self.client.get(f'{self.url}{pk}/')
        self.assertEqual(res.status_code, 200)

        actual = res.json()

        expected_data = getattr(self, f'group{group_number}_json')
        expected = json.dumps(expected_data)

        self.assertJSONEqual(expected, actual)

    @freeze_time(default_time)
    def test__post(self):
        group_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        self.client.force_authenticate(user=user)

        res = self.client.post(self.url, {'name': group_name})
        self.assertEqual(res.status_code, 201)

        # Check response
        actual = res.json()
        self.assertIn('pk', actual.keys())
        actual.pop('pk')

        expected_data = json.dumps({
            'name': group_name,
            'owner': self.get_user_json(user),
            'members': [
                self.get_user_json(user),
            ],
            'create_time': default_time
        })

        self.assertJSONEqual(expected_data, actual)

        # Check DB
        group = Group.objects.filter(name=group_name).first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, group_name)
        self.assertEqual(group.owner, user)

        members = group.members.all()
        self.assertEqual(len(members), 1)
        self.assertIn(user, members)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch(self, method):
        self.client.force_authenticate(user=self.owner)
        group_name = fake.text(max_nb_chars=150)

        url = f'{self.url}{self.group1.pk}/'
        req_method = getattr(self.client, method)
        res = req_method(url, {'name': group_name})
        self.assertEqual(res.status_code, 200)

        # Check response
        actual = res.json()
        self.assertIn('pk', actual.keys())
        actual.pop('pk')

        expected_data = json.dumps({
            'name': group_name,
            'owner': self.get_user_json(self.owner),
            'members': [
                self.get_user_json(self.owner),
                self.get_user_json(self.members[0]),
                self.get_user_json(self.members[1]),
            ],
            'create_time': self.group1_create_time
        })

        self.assertJSONEqual(expected_data, actual)

        # Check DB
        group = Group.objects.filter(name=group_name).first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, group_name)
        self.assertEqual(group.owner, self.owner)

        members = group.members.all()
        self.assertEqual(len(members), 3)
        self.assertIn(self.owner, members)

    def test__delete(self):
        self.client.force_authenticate(user=self.owner)

        url = f'{self.url}{self.group1.pk}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Group.objects.filter(pk=self.group1.pk).exists())

    def test__get_list_permission(self):
        user = baker.make(User)
        group3 = baker.make(Group, owner=user)
        group3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)
        data = res.json()

        self.assertEqual(len(data), 1)
        pks = [group['pk'] for group in data]
        self.assertNotIn(self.group1.pk, pks)
        self.assertNotIn(self.group2.pk, pks)
        self.assertIn(group3.pk, pks)

    def test__get_detail_permission(self):
        user = baker.make(User)
        group3 = baker.make(Group, owner=user)
        group3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.get(f'{self.url}{group3.pk}/')
        self.assertEqual(res.status_code, 200)

        for group in [self.group1, self.group2]:
            res = self.client.get(f'{self.url}{group.pk}/')
            self.assertEqual(res.status_code, 404)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch_permission(self, method):
        group_name = fake.text(max_nb_chars=150)
        user = baker.make(User)
        group3 = baker.make(Group, owner=user)
        group3.members.add(user)

        self.client.force_authenticate(user=user)
        req_method = getattr(self.client, method)
        res = req_method(f'{self.url}{group3.pk}/', {'name': group_name})
        self.assertEqual(res.status_code, 200)

        for group in [self.group1, self.group2]:
            res = req_method(f'{self.url}{group.pk}/', {'name': group_name})
            self.assertEqual(res.status_code, 404)

    def test__delete_permission(self):
        user = baker.make(User)
        group3 = baker.make(Group, owner=user)
        group3.members.add(user)

        self.client.force_authenticate(user=user)
        res = self.client.delete(f'{self.url}{group3.pk}/')
        self.assertEqual(res.status_code, 204)

        for group in [self.group1, self.group2]:
            res = self.client.delete(f'{self.url}{group.pk}/')
            self.assertEqual(res.status_code, 404)

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
