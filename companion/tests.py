from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from model_bakery import baker

User = get_user_model()


class CompanionTestCase(APITestCase):
    def test_language_vietnamese(self):
        user = baker.make(User)
        self.client.force_authenticate(user=user)

        res = self.client.post('/split-the-bill/events/', **{'HTTP_ACCEPT_LANGUAGE': 'vi'})
        data = res.json()
        self.assertListEqual(data['name'], ['Trường này là bắt buộc.'])

    def test_browsable_api_only_allowed_for_staffs(self):
        user = baker.make(User, is_staff=False)
        self.client.force_authenticate(user=user)
        res = self.client.get('/split-the-bill/events/?format=api')
        self.assertEqual(res.content, b'')

        user = baker.make(User, is_staff=True)
        self.client.force_authenticate(user=user)
        res = self.client.get('/split-the-bill/events/?format=api')
        self.assertNotEqual(res.content, b'')
