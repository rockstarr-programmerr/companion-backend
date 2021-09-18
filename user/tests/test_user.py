import json
import random
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from faker import Faker
from model_bakery import baker
from parameterized import parameterized
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from companion.utils.testing import MediaTestCase
from split_the_bill.models import Event, EventInvitation
from split_the_bill.utils.datetime import format_iso
from user.views import UserEventInvitationViewSet

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
            'nickname': user.nickname,
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
            users.sort(key=lambda user: user.nickname)
        else:
            event = getattr(self, f'event{event_number}')
            user = random.choice(getattr(self, f'members{event_number}'))
            users = event.members.all().order_by('nickname')

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


class UserUpdateTestCase(MediaTestCase, _UserTestCase):
    @parameterized.expand([
        ['put'],
        ['patch'],
    ])
    def test__put_and_patch(self, method):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        url = self.get_detail_url(user.pk)
        req_method = getattr(self.client, method)

        new_nickname = fake.text(max_nb_chars=10)
        new_email = fake.email()
        data = {
            'nickname': new_nickname,
            'email': new_email,
        }
        res = req_method(url, data)
        self.assertEqual(res.status_code, 200)

        # Test DB
        user.refresh_from_db()
        self.assertEqual(user.nickname, new_nickname)
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

        new_nickname = fake.text(max_nb_chars=10)
        new_email = fake.email()
        data = {
            'nickname': new_nickname,
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

        email = fake.email()
        password = fake.password()

        res = self.client.post(self.url, {'email': email, 'password': password})
        self.assertEqual(res.status_code, 201)

        # Check response
        actual = res.json()
        expected = json.dumps({
            'email': email,
        })
        self. assertJSONEqual(expected, actual)

        # Check DB
        user = User.objects.filter(email=email).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.nickname, email.split('@')[0])

        # Check if this user can now be authenticate with that password
        res = self.client.post(self.login_url, {'email': email, 'password': password})
        data = res.json()
        access_token = data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        res = self.client.get(self.my_info_url)
        self.assertEqual(res.status_code, 200)


class UserMyInfoTestCase(MediaTestCase, _UserTestCase):
    url = reverse('user-list')
    my_info_url = reverse('user-my-info')

    def get_user_json(self, pk, request=None):
        user_json = super().get_user_json(pk, request=request)
        user_json.update({
            'event_invitations_url': reverse('user-my-event-invitation-list', request=request)
        })
        return user_json

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
        nickname = fake.text(max_nb_chars=150)
        email = fake.email()

        req_method = getattr(self.client, method)
        res = req_method(self.my_info_url, {'nickname': nickname, 'email': email})
        self.assertEqual(res.status_code, 200)

        # Check DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, nickname)
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

    def test__bug__cannot_patch(self):
        self.client.force_authenticate(user=self.user)
        email = fake.email()
        data = {'email': email}
        res = self.client.patch(self.my_info_url, data)
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, email)

    def test__remove_avatar(self):
        """
        If you has both `avatar` and `social_avatar_url`,
        then when they remove `avatar`, `social_avatar_url` will also be remove
        """
        self.client.force_authenticate(user=self.user)
        url = self.my_info_url

        avatar_path = Path(__file__).parent / 'assets' / 'avatar.jpg'
        with open(avatar_path, 'rb') as avatar:
            data = {'avatar': avatar}
            self.client.patch(url, data, format='multipart')

        social_avatar_url = fake.url()
        self.user.social_avatar_url = social_avatar_url
        self.user.save()

        self.client.patch(url, {'avatar': None})
        self.user.refresh_from_db()
        with self.assertRaises(ValueError):
            self.user.avatar.path
            self.user.avatar_thumbnail.path
        self.assertEqual(self.user.avatar_thumbnail, '')
        self.assertEqual(self.user.social_avatar_url, '')


class UserSearchTestCase(_UserTestCase):
    url = reverse('user-search')

    def setUp(self):
        super().setUp(create_data=False)
        baker.make(User, nickname='Carl Johnson', email='johnson@grove.street')
        baker.make(User, nickname='BigSmoke', email='bigsmoke@grove.street')
        baker.make(User, nickname='Sweet', email='king@grove.street')
        baker.make(User, nickname='Ryder', email='ryder@grove.street')
        baker.make(User, nickname='Brian', email='brian@sweet.street')
        baker.make(User, nickname='BigBear', email='bigbear@grove.street')
        baker.make(User, nickname='LittleBear', email='littlebear@grove.street')

    @parameterized.expand([
        ['big', ['bigsmoke@grove.street', 'bigbear@grove.street']],
        ['bear', ['bigbear@grove.street', 'littlebear@grove.street']],
        ['arl', ['johnson@grove.street']],
        ['The Truth', []],
        ['king', ['king@grove.street']],
        ['sweet', ['king@grove.street', 'brian@sweet.street']],
    ])
    def test__search(self, query, expected_emails):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        data = {'nickname_or_email__icontains': query}
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 200)

        users = User.objects.filter(email__in=expected_emails).order_by('nickname')
        actual = res.json()
        expected = json.dumps(self.get_pagination_json([
            {
                'nickname': user.nickname,
                'email': user.email,
                'avatar_thumbnail': None,
            }
            for user in users
        ], extra_actions=False))
        self.assertJSONEqual(expected, actual)

    def test__search__dont_find_yourself(self):
        user = baker.make(User)
        self.client.force_authenticate(user=user)
        data = {'nickname_or_email__icontains': user.nickname}
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps(self.get_pagination_json([], extra_actions=False))
        self.assertJSONEqual(expected, actual)

    def test__search_permission(self):
        data = {'nickname_or_email__icontains': 'something'}

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 401)

    def test__validation(self):
        user = User.objects.first()
        self.client.force_authenticate(user=user)
        data = {'nickname_or_email__icontains': ''}
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'nickname_or_email__icontains': ['This field is required.']})


class UserMyEventInvitationTestCase(_UserTestCase):
    def setUp(self):
        super().setUp()
        self.user = baker.make(User)
        self.event1.invited_users.add(self.user)
        self.event2.invited_users.add(self.user)
        self.client.force_authenticate(user=self.user)

    def get_invitation_json(self, invitation, request=None):
        return {
            'url': reverse('user-my-event-invitation-detail', kwargs={'pk': invitation.pk}, request=request),
            'pk': invitation.pk,
            'event': {
                'name': invitation.event.name,
                'creator': {
                    'nickname': invitation.event.creator.nickname,
                    'email': invitation.event.creator.email,
                    'avatar': invitation.event.creator.avatar.url if invitation.event.creator.avatar else None,
                    'avatar_thumbnail': invitation.event.creator.avatar_thumbnail.url if invitation.event.creator.avatar_thumbnail else None,
                }
            },
            'status': invitation.status,
            'create_time': format_iso(invitation.create_time),
            'update_time': format_iso(invitation.update_time),
            'accept_invitation_url': reverse('user-my-event-invitation-accept', kwargs={'pk': invitation.pk}, request=request),
            'decline_invitation_url': reverse('user-my-event-invitation-decline', kwargs={'pk': invitation.pk}, request=request)
        }

    def test__list_my_event_invitations(self):
        url = reverse('user-my-event-invitation-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        invitations = EventInvitation.objects.filter(user=self.user).order_by('-create_time')
        results = [
            self.get_invitation_json(invitation, request=res.wsgi_request)
            for invitation in invitations
        ]
        expected = json.dumps(
            self.get_pagination_json(results, extra_actions=False),
        )
        actual = res.json()

        self.assertJSONEqual(expected, actual)

    def test__retrieve_my_event_invitation(self):
        invitation = EventInvitation.objects.filter(user=self.user).first()
        url = reverse('user-my-event-invitation-detail', kwargs={'pk': invitation.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        actual = res.json()
        expected = json.dumps(
            self.get_invitation_json(invitation, request=res.wsgi_request)
        )

        self.assertJSONEqual(expected, actual)

    def test__accept_invitation(self):
        invitation = EventInvitation.objects.filter(user=self.user, event=self.event1).first()
        self.assertEqual(invitation.status, 'pending')
        self.assertNotIn(self.user, self.event1.members.all())

        url = reverse('user-my-event-invitation-accept', kwargs={'pk': invitation.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'accepted')
        self.assertIn(self.user, self.event1.members.all())

    def test__decline_invitation(self):
        invitation = EventInvitation.objects.filter(user=self.user, event=self.event2).first()
        self.assertEqual(invitation.status, 'pending')
        self.assertNotIn(self.user, self.event2.members.all())

        url = reverse('user-my-event-invitation-decline', kwargs={'pk': invitation.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'declined')
        self.assertNotIn(self.user, self.event2.members.all())

    def test__filter_and_ordering(self):
        self.assertListEqual(UserEventInvitationViewSet.ordering_fields, ['create_time', 'update_time', 'event__name', 'status'])
        self.assertListEqual(UserEventInvitationViewSet.ordering, ['-create_time'])

    def test__get_list_permission(self):
        url = reverse('user-my-event-invitation-list')

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 401)

        # Cannot see other's invitations
        other_user = baker.make(User)
        self.event1.invited_users.add(other_user)
        invitation_pks = EventInvitation.objects.filter(user=other_user).values_list('pk', flat=True)

        self.client.force_authenticate(user=self.user)
        res = self.client.get(url)
        pks = [data['pk'] for data in res.json()['results']]

        for pk in invitation_pks:
            self.assertNotIn(pk, pks)

    @parameterized.expand([
        ['detail', 'get'],
        ['accept', 'post'],
        ['decline', 'post'],
    ])
    def test__get_detail__and__accept_decline__permission(self, action, method):
        invitation = EventInvitation.objects.filter(user=self.user).first()
        url = reverse(f'user-my-event-invitation-{action}', kwargs={'pk': invitation.pk})
        req_method = getattr(self.client, method)

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = req_method(url)
        self.assertEqual(res.status_code, 401)

        # Other user cannot see
        other_user = baker.make(User)
        self.client.force_authenticate(user=other_user)
        res = req_method(url)
        self.assertEqual(res.status_code, 404)

        # Correct user can see
        self.client.force_authenticate(user=self.user)
        res = req_method(url)
        self.assertEqual(res.status_code, 200)
