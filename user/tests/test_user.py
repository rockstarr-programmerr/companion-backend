import json
from model_bakery import baker
from faker import Faker
from parameterized import parameterized

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()
fake = Faker()


class UserTestCase(APITestCase):
    url = '/users/'

    def setUp(self):
        super().setUp()
        self.user = baker.make(User)
        self.client.force_authenticate(user=self.user)

    def test__no_user_endpoint_exposed(self):
        list_url = self.url
        detail_url = f'{self.url}{self.user.pk}/'

        endpoints = {
            'get': list_url,
            'get': detail_url,
            'post': detail_url,
            'put': detail_url,
            'patch': detail_url,
            'delete': detail_url,
        }
        for method, url in endpoints.items():
            req_method = getattr(self.client, method)
            res = req_method(url)
            self.assertEqual(res.status_code, 404)


class UserInfoTestCase(APITestCase):
    url = '/users/'
    get_info_url = url + 'get-my-info/'
    update_info_url = url + 'update-my-info/'

    def setUp(self):
        super().setUp()
        self.user = baker.make(User)
        self.client.force_authenticate(user=self.user)

    def test__get_my_info(self):
        res = self.client.get(self.get_info_url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps({
            'username': self.user.username,
            'email': self.user.email,
        })

        self.assertJSONEqual(expected, actual)

    @parameterized.expand([
        ['post'],
        ['put'],
        ['patch'],
    ])
    def test__update_my_info(self, method):
        username = fake.text(max_nb_chars=150)
        email = fake.email()

        req_method = getattr(self.client, method)
        res = req_method(self.update_info_url, {'username': username, 'email': email})
        self.assertEqual(res.status_code, 200)

        # Check response
        actual = res.json()
        expected = json.dumps({
            'username': username,
            'email': email,
        })
        self. assertJSONEqual(expected, actual)

        # Check DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, username)
        self.assertEqual(self.user.email, email)

    @parameterized.expand([
        ['get', get_info_url],
        ['post', update_info_url],
        ['put', update_info_url],
        ['patch', update_info_url],
    ])
    def test__unauthenticated_user_cannot_access(self, method, url):
        self.client.force_authenticate(user=None)
        req_method = getattr(self.client, method)
        res = req_method(url)
        self.assertEqual(res.status_code, 401)


class UserRegisterTestCase(APITestCase):
    url = '/users/register/'
    login_url = '/users/login/'
    get_info_url = '/users/get-my-info/'

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
