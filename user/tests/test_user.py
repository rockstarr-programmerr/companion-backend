import json
import random
from pathlib import Path

from django.contrib.auth import get_user_model
from django.conf import settings
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

    def setUp(self, *args, **kwargs):
        super().setUp()

        if kwargs.get('create_data', True):
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
            'avatar_thumbnail': user.avatar_thumbnail.path if user.avatar_thumbnail else None,
        }

    @staticmethod
    def get_pagination_json(results, count=None, next=None, previous=None, request=None, extra_actions=True):
        if count is None:
            count = len(results)

        response = {
            'count': count,
            'next': next,
            'previous': previous,
            'results': results,
        }

        if extra_actions:
            response['extra_action_urls'] = {
                'my_info': reverse('user-my-info', request=request),
                'register': reverse('user-register', request=request),
                'search': reverse('user-search', request=request),
            }

        return response

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


class UserUpdateTestCase(_UserTestCase):
    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch(self, method):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        url = self.get_detail_url(user.pk)
        req_method = getattr(self.client, method)

        new_username = fake.text(max_nb_chars=10)
        new_email = fake.email()
        data = {
            'username': new_username,
            'email': new_email,
        }
        res = req_method(url, data)
        self.assertEqual(res.status_code, 200)

        # Test DB
        user.refresh_from_db()
        self.assertEqual(user.username, new_username)
        self.assertEqual(user.email, new_email)

        # Test Response
        actual = res.json()
        expected = json.dumps(
            self.get_user_json(user, request=res.wsgi_request)
        )
        self.assertJSONEqual(expected, actual)

    def test__update_avatar(self):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        url = self.get_detail_url(user.pk)

        avatar_path = Path(__file__).parent / 'assets' / 'avatar.jpg'
        with open(avatar_path, 'rb') as avatar:
            data = {'avatar': avatar}
            res = self.client.patch(url, data, format='multipart')

        results = res.json()

        # Check if resizing works
        user.refresh_from_db()
        self.assertLessEqual(user.avatar.width, 256)
        self.assertLessEqual(user.avatar.height, 256)
        self.assertLessEqual(user.avatar_thumbnail.width, 64)
        self.assertLessEqual(user.avatar_thumbnail.height, 64)

        # Check if path returned to client is correct
        avatar_path = Path(user.avatar.path).relative_to(settings.MEDIA_ROOT)
        avatar_path = str(avatar_path).replace('\\', '/')
        avatar_url = 'http://testserver' + settings.MEDIA_URL + avatar_path
        self.assertEqual(avatar_url, results['avatar'])

        avatar_thumbnail_path = Path(user.avatar_thumbnail.path).relative_to(settings.MEDIA_ROOT)
        avatar_thumbnail_path = str(avatar_thumbnail_path).replace('\\', '/')
        avatar_thumbnail_url = 'http://testserver' + settings.MEDIA_URL + avatar_thumbnail_path
        self.assertEqual(avatar_thumbnail_url, results['avatar_thumbnail'])

    def test__remove_avatar(self):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        url = self.get_detail_url(user.pk)

        avatar_path = Path(__file__).parent / 'assets' / 'avatar.jpg'
        with open(avatar_path, 'rb') as avatar:
            data = {'avatar': avatar}
            res = self.client.patch(url, data, format='multipart')

        user.refresh_from_db()
        self.assertIsNotNone(user.avatar)
        self.assertIsNotNone(user.avatar_thumbnail)
        self.assertIsNotNone(res.json()['avatar'])
        self.assertIsNotNone(res.json()['avatar_thumbnail'])

        data = {'avatar': None}
        res = self.client.patch(url, data)

        user.refresh_from_db()
        with self.assertRaises(ValueError):
            user.avatar.path
            user.avatar_thumbnail.path
        self.assertIsNone(res.json()['avatar'])
        self.assertIsNone(res.json()['avatar_thumbnail'])

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch__permission(self, method):
        req_method = getattr(self.client, method)

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        url = self.get_detail_url(self.creator1.pk)
        res = req_method(url)
        self.assertEqual(res.status_code, 401)

        # User cannot update info of others
        self.client.force_authenticate(user=self.creator1)
        other_user = random.choice(self.event1.members.exclude(pk=self.creator1.pk))
        url = self.get_detail_url(other_user.pk)
        res = req_method(url)
        self.assertEqual(res.status_code, 403)

    def test_bug__user_cannot_update__or__see_detail__if_not_join_event(self):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        url = self.get_detail_url(user.pk)

        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        new_username = fake.text(max_nb_chars=10)
        new_email = fake.email()
        data = {
            'username': new_username,
            'email': new_email,
        }
        res = self.client.put(url, data)
        self.assertEqual(res.status_code, 200)

        res = self.client.patch(url, data)
        self.assertEqual(res.status_code, 200)


class UserNotAllowedMethodTestCase(_UserTestCase):
    @parameterized.expand([
        ['post', False],
        ['delete', True],
    ])
    def test_method_not_allowed(self, method, is_detail):
        req_method = getattr(self.client, method)
        user = baker.make(User)
        if is_detail:
            url = self.get_detail_url(user.pk)
        else:
            url = self.url

        self.client.force_authenticate(user=user)
        res = req_method(url)
        self.assertEqual(res.status_code, 405)


class UserRegisterTestCase(APITestCase):
    url = reverse('user-register')
    login_url = reverse('token_obtain_pair')
    my_info_url = reverse('user-my-info')

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

        res = self.client.get(self.my_info_url)
        self.assertEqual(res.status_code, 200)


class UserMyInfoTestCase(_UserTestCase):
    url = reverse('user-list')
    my_info_url = reverse('user-my-info')

    def setUp(self):
        super().setUp(create_data=False)
        self.user = baker.make(User)
        self.client.force_authenticate(user=self.user)

    def test__get_my_info(self):
        res = self.client.get(self.my_info_url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps(
            self.get_user_json(self.user.pk, request=res.wsgi_request)
        )

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__update_my_info(self, method):
        username = fake.text(max_nb_chars=150)
        email = fake.email()

        req_method = getattr(self.client, method)
        res = req_method(self.my_info_url, {'username': username, 'email': email})
        self.assertEqual(res.status_code, 200)

        # Check DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, username)
        self.assertEqual(self.user.email, email)

        # Check response
        actual = res.json()
        expected = json.dumps(
            self.get_user_json(self.user.pk, request=res.wsgi_request)
        )
        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        ['get'],
        ['put'],
        ['patch'],
    ])
    def test__unauthenticated_user_cannot_access(self, method):
        self.client.force_authenticate(user=None)
        req_method = getattr(self.client, method)
        res = req_method(self.my_info_url)
        self.assertEqual(res.status_code, 401)

    @parameterized.expand([
        ['post'],
        ['delete'],
    ])
    def test__method_not_allowed(self, method):
        self.client.force_authenticate(user=self.user)
        req_method = getattr(self.client, method)
        res = req_method(self.my_info_url)
        self.assertEqual(res.status_code, 405)


class UserSearchTestCase(_UserTestCase):
    url = reverse('user-search')

    def setUp(self):
        super().setUp(create_data=False)
        baker.make(User, username='Carl Johnson')
        baker.make(User, username='BigSmoke')
        baker.make(User, username='Sweet')
        baker.make(User, username='Ryder')
        baker.make(User, username='Brian')
        baker.make(User, username='BigBear')
        baker.make(User, username='LittleBear')

    @parameterized.expand([
        ['big', ['BigSmoke', 'BigBear']],
        ['bear', ['BigBear', 'LittleBear']],
        ['arl', ['Carl Johnson']],
        ['The Truth', []],
    ])
    def test__search(self, query, expected_usernames):
        user = User.objects.first()
        self.client.force_authenticate(user=user)
        data = {'username__icontains': query}
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 200)

        expected_usernames.sort()
        actual = res.json()
        expected = json.dumps(self.get_pagination_json([
            {
                'username': username,
                'avatar_thumbnail': None,
            }
            for username in expected_usernames
        ], extra_actions=False))
        self.assertJSONEqual(expected, actual)

    def test__search_permission(self):
        data = {'username__icontains': 'something'}

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 401)

    def test__validation(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)
        data = {'username__icontains': 'ab'}
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'username__icontains': ['Ensure this value has at least 3 characters (it has 2).']})
