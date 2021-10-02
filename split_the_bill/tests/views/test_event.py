import json
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker
from parameterized import parameterized
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from companion.utils.datetime import format_iso
from companion.utils.testing import MediaTestCase
from split_the_bill.models import Event, EventInvitation
from companion.utils.url import update_url_params
from split_the_bill.views import EventViewSet

fake = Faker()
User = get_user_model()

URL = '/split-the-bill/events/'
EVENT1_CREATE_TIME = timezone.now().replace(day=15)
EVENT2_CREATE_TIME = EVENT1_CREATE_TIME + timedelta(days=1)
DEFAULT_TIME = EVENT2_CREATE_TIME + timedelta(days=1)


class _EventViewSetTestCase(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.creator = baker.make(User)
        self.members = baker.make(User, _quantity=4)
        dummy_request = APIRequestFactory().get('')

        with freeze_time(EVENT1_CREATE_TIME):
            self.event1 = baker.make(Event, creator=self.creator)
            self.event1.members.add(self.creator, *self.members[:2])
            self.event1.create_qr_code(dummy_request)

        with freeze_time(EVENT2_CREATE_TIME):
            self.event2 = baker.make(Event, creator=self.creator)
            self.event2.members.add(self.creator, *self.members[2:])
            self.event2.create_qr_code(dummy_request)

    def get_event1_json(self, request):
        return self.get_event_json(self.event1, request)

    def get_event2_json(self, request):
        return self.get_event_json(self.event2, request)

    def get_event_json(self, event, request):
        members = event.members.all()

        transactions_url = reverse('transaction-list', request=request)
        transactions_url = update_url_params(transactions_url, {'event': event.pk})

        invitations_url = reverse('event-invitation-list', request=request)
        invitations_url = update_url_params(invitations_url, {'event': event.pk})

        return {
            'url': reverse('event-detail', kwargs={'pk': event.pk}, request=request),
            'pk': event.pk,
            'name': event.name,
            'creator': self.get_user_json(event.creator, request=request),
            'qr_code': f'http://testserver{event.qr_code.url}',
            'members': [
                self.get_user_json(member, request=request)
                for member in members
            ],
            'create_time': format_iso(event.create_time),
            'transactions_url': transactions_url,
            'invitations_url': invitations_url,
            'extra_action_urls': {
                'invite_members': reverse('event-invite-members', kwargs={'pk': event.pk}, request=request),
                'cancel_invite_members': reverse('event-cancel-invite-members', kwargs={'pk': event.pk}, request=request),
                'remove_members': reverse('event-remove-members', kwargs={'pk': event.pk}, request=request),
                'reset_qr': reverse('event-reset-qr', kwargs={'pk': event.pk}, request=request),
                'chart_info': reverse('event-chart-info', kwargs={'pk': event.pk}, request=request),
                'settle_expenses': reverse('event-settle-expenses', kwargs={'pk': event.pk}, request=request),
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
            'nickname': user.nickname,
            'email': user.email,
            'avatar': user.avatar.path if user.avatar else None,
            'avatar_thumbnail': user.avatar_thumbnail.path if user.avatar_thumbnail else None,
        }

    @staticmethod
    def get_pagination_json(results, request, count=None, next=None, previous=None):
        if count is None:
            count = len(results)

        return {
            'count': count,
            'next': next,
            'previous': previous,
            'results': results,
            'extra_action_urls': {
                'join_with_qr': reverse('event-join-with-qr', request=request)
            }
        }

    def get_invite_members_url(self, pk):
        return reverse('event-invite-members', kwargs={'pk': pk})

    def get_cancel_invite_members_url(self, pk):
        return reverse('event-cancel-invite-members', kwargs={'pk': pk})

    def get_remove_members_url(self, pk):
        return reverse('event-remove-members', kwargs={'pk': pk})


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
        expected = json.dumps(self.get_pagination_json(results, res.wsgi_request))

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


class EventRemoveMembersTestCase(_EventViewSetTestCase):
    def test__remove_members(self):
        self.client.force_authenticate(user=self.creator)

        new_members = baker.make(User, _quantity=3)
        self.event1.members.add(*new_members)
        for member in new_members:
            EventInvitation.objects.create(
                event=self.event1,
                user=member,
                status=EventInvitation.Statuses.ACCEPTED
            )
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

        # After remove members, invitations are also removed
        self.assertFalse(EventInvitation.objects.filter(event=self.event1, user__in=new_members).exists())

    def test__remove_members_validations(self):
        self.client.force_authenticate(user=self.creator)
        url = self.get_remove_members_url(self.event1.pk)

        # 'member_pks' is empty
        data = {'member_pks': []}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': ['This list may not be empty.']})

        # More than 100 'member_pks'
        data = {'member_pks': list(range(1, 102))}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': ['Ensure this field has no more than 100 elements.']})

        # member_pk < 1
        data = {'member_pks': [1, 2, 3, -1]}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': {'3': ['Ensure this value is greater than or equal to 1.']}})

    def test__cannot_remove_creator_of_event(self):
        self.client.force_authenticate(user=self.creator)
        url = self.get_remove_members_url(self.event1.pk)

        data = {'member_pks': [self.creator.pk]}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_pks': ['Cannot remove creator of event.']})

        self.assertIn(self.creator, self.event1.members.all())

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


class EventInvitationTestCase(_EventViewSetTestCase):
    def test__invite_members(self):
        users = baker.make(User, _quantity=3)
        emails = [user.email for user in users]
        event = self.event1
        invited_users = event.invited_users.all()
        for user in users:
            self.assertNotIn(user, invited_users)

        self.client.force_authenticate(user=event.creator)
        url = self.get_invite_members_url(event.pk)
        data = {'member_emails': emails}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)

        invited_users = event.invited_users.all()
        for user in users:
            self.assertIn(user, invited_users)

    def test__cancel_invite_members(self):
        users = baker.make(User, _quantity=3)
        emails = [user.email for user in users]
        event = self.event1
        event.invited_users.add(*users)

        invited_users = event.invited_users.all()
        for user in users:
            self.assertIn(user, invited_users)

        self.client.force_authenticate(user=event.creator)
        url = self.get_cancel_invite_members_url(event.pk)
        data = {'member_emails': emails}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)

        invited_users = event.invited_users.all()
        for user in users:
            self.assertNotIn(user, invited_users)

    def test__invite_validation__already_a_member(self):
        users = baker.make(User, _quantity=3)
        emails = [user.email for user in users]
        event = self.event1
        event.invited_users.add(*users)

        self.client.force_authenticate(user=event.creator)
        url = self.get_invite_members_url(event.pk)
        data = {'member_emails': emails}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)

        msg_arg = ', '.join(emails)
        self.assertDictEqual(res.json(), {'member_emails': [f'These users are already invited: {msg_arg}.']})

    def test__invite_validation__already_is_creator(self):
        event = self.event1
        self.client.force_authenticate(user=event.creator)
        url = self.get_invite_members_url(event.pk)
        data = {'member_emails': [event.creator.email]}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)
        self.assertDictEqual(res.json(), {'member_emails': [f'This user is already the creator of the event: {event.creator.email}.']})

    def test__cancel_invite_validation__not_invited(self):
        users = baker.make(User, _quantity=3)
        emails = [user.email for user in users]
        event = self.event1

        self.client.force_authenticate(user=event.creator)
        url = self.get_cancel_invite_members_url(event.pk)
        data = {'member_emails': emails}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)

        msg_arg = ', '.join(emails)
        self.assertDictEqual(res.json(), {'member_emails': [f'These users are not invited: {msg_arg}.']})

    def test__cancel_invite_validation__invitation_accepted(self):
        users = baker.make(User, _quantity=3)
        emails = [user.email for user in users]
        event = self.event1
        event.invited_users.add(*users)

        status = EventInvitation.Statuses.ACCEPTED
        invitations = EventInvitation.objects.filter(user__email__in=emails)
        invitations.update(status=status)

        self.client.force_authenticate(user=event.creator)
        url = self.get_cancel_invite_members_url(event.pk)
        data = {'member_emails': emails}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 400)

        msg_arg = ', '.join(invitation.user.email for invitation in invitations)
        self.assertDictEqual(res.json(), {'member_emails': [f'These users already accepted their invitations: {msg_arg}.']})

    @parameterized.expand([
        ['invite'],
        ['cancel_invite'],
    ])
    def test__invite_or_cancel_invite__permission(self, action):
        users = baker.make(User, _quantity=3)
        emails = [user.email for user in users]
        event = self.event2
        url = getattr(self, f'get_{action}_members_url')(event.pk)
        data = {'member_emails': emails}

        if action == 'cancel_invite':
            event.invited_users.add(*users)

        # Unauthenticated user cannot access
        self.client.force_authenticate(user=None)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 401)

        # Member cannot invite/cancel-invite
        member = random.choice(event.members.exclude(pk=event.creator.pk))
        self.client.force_authenticate(user=member)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 403)

        # Other event's creator/member cannot access
        other_creator = baker.make(User)
        other_members = baker.make(User, _quantity=2)
        other_event = baker.make(Event, creator=other_creator)
        other_event.members.add(other_creator, *other_members)

        member = random.choice(other_members)
        for user in [other_creator, member]:
            self.client.force_authenticate(user=member)
            res = self.client.post(url, data)
            self.assertEqual(res.status_code, 404)

        invited_users = event.invited_users.all()
        for user in invited_users:
            if action == 'invite':
                self.assertNotIn(user, invited_users)
            else:
                self.assertIn(user, invited_users)

        # Creator can invite/cancel-invite
        self.client.force_authenticate(user=event.creator)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200)

        invited_users = event.invited_users.all()
        for user in invited_users:
            if action == 'invite':
                self.assertIn(user, invited_users)
            else:
                self.assertNotIn(user, invited_users)
