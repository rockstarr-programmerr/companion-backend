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
