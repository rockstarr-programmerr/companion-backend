import json
import random

from django.contrib.auth import get_user_model
from faker import Faker
from model_bakery import baker
from parameterized import parameterized
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from split_the_bill.models import Event

User = get_user_model()
fake = Faker()


class _UserTestCase(APITestCase):
    url = reverse('user-list')

    def setUp(self):
        super().setUp()

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
    def get_pagination_json(results, count=None, next=None, previous=None, request=None):
        if count is None:
            count = len(results)

        return {
            'count': count,
            'next': next,
            'previous': previous,
            'results': results,
            'extra_action_urls': {
                'my_info': reverse('user-my-info', request=request),
                'register': reverse('user-register', request=request),
                'search': reverse('user-search', request=request),
            }
        }

    @staticmethod
    def get_detail_url(pk, request=None):
        return reverse('user-detail', kwargs={'pk': pk}, request=request)


class UserReadTestCase(_UserTestCase):
    @parameterized.expand([
        [1, False],
        [2, False],
        [1, True],
        [2, True],
    ])
    def test__get_list(self, event_number, is_share_member):
        if is_share_member:
            user = random.choice(self.share_members)
            users = list(self.event1.members.all()) + list(self.event2.members.all())
            users = list(set(users))  # Make unique
            users.sort(key=lambda user: user.username)
        else:
            event = getattr(self, f'event{event_number}')
            user = random.choice(getattr(self, f'members{event_number}'))
            users = event.members.all().order_by('username')

        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        results = self.get_pagination_json(
            [
                self.get_user_json(u, request=res.wsgi_request)
                for u in users
            ],
            request=res.wsgi_request
        )
        expected = json.dumps(results)

        self.assertJSONEqual(expected, actual)

    def test__get_detail(self):
        user = self.creator1
        url = self.get_detail_url(user.pk)
        self.client.force_authenticate(user=user)

        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps(
            self.get_user_json(user, request=res.wsgi_request)
        )
        self.assertJSONEqual(expected, actual)

    def test__get_list_permission(self):
        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

        # User of 1 event cannot see user of other events
        members = self.event1.members.exclude(pk__in=[member.pk for member in self.share_members])
        user = random.choice(members)
        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)

        pks = [data['pk'] for data in res.json()['results']]
        other_pks = self.event2.members.exclude(pk__in=[member.pk for member in self.share_members]).values_list('pk', flat=True)
        for pk in other_pks:
            self.assertNotIn(pk, pks)

    def test__get_detail_permission(self):
        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

        # User of 1 event cannot see user of other events
        members = self.event1.members.exclude(pk__in=[member.pk for member in self.share_members])
        user = random.choice(members)
        self.client.force_authenticate(user=user)
        res = self.client.get(self.url)

        other_members = self.event2.members.exclude(pk__in=[member.pk for member in self.share_members])
        other_member = random.choice(other_members)

        url = self.get_detail_url(other_member.pk)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

        # Users can see other users of their events
        member = random.choice(members)
        url = self.get_detail_url(member.pk)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)


# class UserInfoTestCase(APITestCase):
#     url = '/users/'
#     get_info_url = url + 'get-my-info/'
#     update_info_url = url + 'update-my-info/'

#     def setUp(self):
#         super().setUp()
#         self.user = baker.make(User)
#         self.client.force_authenticate(user=self.user)

#     def test__get_my_info(self):
#         res = self.client.get(self.get_info_url)
#         self.assertEqual(res.status_code, 200)

#         actual = res.json()
#         expected = json.dumps({
#             'username': self.user.username,
#             'email': self.user.email,
#         })

#         self.assertJSONEqual(expected, actual)

#     @parameterized.expand([
#         ['post'],
#         ['put'],
#         ['patch'],
#     ])
#     def test__update_my_info(self, method):
#         username = fake.text(max_nb_chars=150)
#         email = fake.email()

#         req_method = getattr(self.client, method)
#         res = req_method(self.update_info_url, {'username': username, 'email': email})
#         self.assertEqual(res.status_code, 200)

#         # Check response
#         actual = res.json()
#         expected = json.dumps({
#             'username': username,
#             'email': email,
#         })
#         self. assertJSONEqual(expected, actual)

#         # Check DB
#         self.user.refresh_from_db()
#         self.assertEqual(self.user.username, username)
#         self.assertEqual(self.user.email, email)

#     @parameterized.expand([
#         ['get', get_info_url],
#         ['post', update_info_url],
#         ['put', update_info_url],
#         ['patch', update_info_url],
#     ])
#     def test__unauthenticated_user_cannot_access(self, method, url):
#         self.client.force_authenticate(user=None)
#         req_method = getattr(self.client, method)
#         res = req_method(url)
#         self.assertEqual(res.status_code, 401)


class UserRegisterTestCase(APITestCase):
    url = '/users/register/'
    login_url = '/users/login/'
    get_info_url = '/users/my-info/'

    def test__register_user(self):
        self.client.force_authenticate(user=None)

        username = fake.text(max_nb_chars=150)
        email = fake.email()
        password = fake.password()

        res = self.client.post(self.url, {'username': username, 'email': email, 'password': password})
        self.assertEqual(res.status_code, 201)

        # Check response
        actual = res.json()
        expected = json.dumps({
            'username': username,
            'email': email,
        })
        self. assertJSONEqual(expected, actual)

        # Check DB
        user = User.objects.filter(username=username).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, email)

        # Check if this user can now be authenticate with that password
        res = self.client.post(self.login_url, {'username': username, 'password': password})
        data = res.json()
        access_token = data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        res = self.client.get(self.get_info_url)
        self.assertEqual(res.status_code, 200)
