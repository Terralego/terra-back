from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.events.models import EventHandler
from terracommon.events.signals import event
from terracommon.events.signals.handlers import (SendNotificationHandler,
                                                 SetGroupHandler,
                                                 TimeDeltaHandler)
from terracommon.trrequests.tests.factories import UserRequestFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class EventsTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.user = TerraUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_newrequest_event(self):
        self.signal_was_called = False

        request = {
            'state': 0,
            'properties': {
                'myproperty': 'myvalue',
            },
            'geojson': {},
        }

        EventHandler.objects.create(
            action='USERREQUEST_CREATED',
            handler='terracommon.events.signals.handlers.SendEmailHandler',

        )

        def handler(sender, **kwargs):
            self.signal_was_called = True
        event.connect(handler)

        self._set_permissions(['can_create_requests', ])
        response = self.client.post(reverse('request-list'),
                                    request,
                                    format='json')
        self.assertEqual(201, response.status_code)
        self.assertTrue(self.signal_was_called)
        event.disconnect(handler)


class TimeDeltaHandlerTestCase(TestCase):

    def setUp(self):
        self.userrequest = UserRequestFactory()

    def test_handler(self):
        daysdelta = '20'

        args = {
            'instance': self.userrequest,
            'user': self.userrequest.owner,
        }

        # test with nested values
        executor = TimeDeltaHandler(
            'USERREQUEST_CREATED',
            {'daysdelta': daysdelta, 'field': 'properties.name.attribute'},
            **args)

        if executor.valid_condition():
            executor()

        self.userrequest.refresh_from_db()

        self.assertEqual(
            self.userrequest.properties['name']['attribute'],
            str(date.today() + timedelta(days=int(daysdelta)))
            )

        # test with expiry field
        executor = TimeDeltaHandler(
            'USERREQUEST_CREATED',
            {'daysdelta': daysdelta, 'field': 'expiry'},
            **args)

        if executor.valid_condition():
            executor()

        self.userrequest.refresh_from_db()

        self.assertEqual(
            self.userrequest.expiry,
            date.today() + timedelta(days=int(daysdelta))
            )


class UserNotificationHandlerTestCase(TestCase):

    def setUp(self):
        self.userrequest = UserRequestFactory()

    def test_handler(self):
        args = {
            'instance': self.userrequest,
            'user': self.userrequest.owner,
        }

        settings = {
            'level': 'DEBUG',
            'message': 'notification {event} {user}',
            'event_code': 'test_notification',
        }

        event = 'USERREQUEST_CREATED'
        # test with nested values
        executor = SendNotificationHandler(
            event,
            settings,
            **args)

        if executor.valid_condition():
            executor()

        self.assertEqual(1, self.userrequest.owner.notifications.count())
        notification = self.userrequest.owner.notifications.first()

        self.assertFalse(notification.read)
        self.assertEqual(
            notification.message,
            f'notification {event} {self.userrequest.owner.email}')
        self.assertEqual(notification.event_code, 'test_notification')


class SetGroupHandlerTestCase(TestCase):

    def setUp(self):
        self.user = TerraUserFactory()
        self.group = Group.objects.create(name="testgroup")

    def test_handler(self):
        args = {
            'instance': self.user,
            'user': self.user,
        }

        # test with nested values
        executor = SetGroupHandler(
            'USER_CREATED',
            {'userfield': 'user', 'group': self.group.name},
            **args)

        if executor.valid_condition():
            executor()

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.groups.first(),
            self.group
            )
