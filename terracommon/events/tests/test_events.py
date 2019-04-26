from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.events.models import EventHandler
from terracommon.events.signals import event
from terracommon.events.signals.handlers import (AbstractHandler,
                                                 ModelValueHandler,
                                                 SendNotificationHandler,
                                                 SetGroupHandler,
                                                 TimeDeltaHandler)
from terracommon.events.tests.factories import UserFactory
from terracommon.trrequests.tests.factories import UserRequestFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class EventsTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.user = UserFactory()
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
        response = self.client.post(reverse('trrequests:request-list'),
                                    request,
                                    format='json')
        self.assertEqual(201, response.status_code)
        self.assertTrue(self.signal_was_called)
        event.disconnect(handler)

    def test_no_instance(self):
        def abstract_instance(self):
            return self.serialized_instance
        AbstractHandler.__call__ = abstract_instance

        # Without instance, handler should not raise an error
        AbstractHandler('TEST_ACTION', {})()


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
        self.user = UserFactory()
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


class ModelValueHandlerTestCase(TestCase):

    def setUp(self):
        UserRequestFactory(
            expiry=date.today(),
        )
        self.userrequest = UserRequestFactory(
            expiry=date.today() + timedelta(days=2),
        )
        UserRequestFactory(
            expiry=date.today() + timedelta(days=3),
        )

        self.handler_settings = {
            'model': 'terracommon.trrequests.models.UserRequest',
            'query': {
                'expiry': 'date.today() + timedelta(days=2)',
            },
            'actions': [
                {'action': 'USERREQUEST_IMPENDING_EXPIRY',
                 'kwargs': {
                     'user': '{instance.reviewers}',
                 }, },
                {'action': 'FAKE_ACTION',
                 'kwargs': {
                     'user': '{instance.reviewers}',
                 }, },
            ]
        }

        self.executor = ModelValueHandler(
            event="EVERY_DAY",
            settings=self.handler_settings,
        )

    def test_event_proxy_calls_by_handler(self):
        event_proxy = MagicMock()
        event.connect(event_proxy)

        if self.executor.valid_condition():
            self.executor()

        self.assertTrue(event_proxy.called)
        self.assertEqual(event_proxy.call_count, 2)
        for i, call in enumerate(event_proxy.call_args_list):
            _, call_args = call
            settings_action = self.handler_settings['actions'][i]
            self.assertEqual(call_args.get('action'),
                             settings_action.get('action'))
            self.assertEqual(call_args.get('instance'), self.userrequest)
            self.assertEqual(call_args.get('sender'), ModelValueHandler)
            self.assertEqual(call_args.get('user'),
                             settings_action['kwargs']['user'])
            self.assertIsNotNone(call_args.get('signal'))  # Not predictable

        event.disconnect(event_proxy)

    def test_actions_are_triggered(self):
        handler_path = 'terracommon.events.signals.handlers.AbstractHandler'

        EventHandler.objects.create(
            action='FAKE_ACTION',
            handler=handler_path,
        )

        with patch(handler_path) as mocked_handler:
            if self.executor.valid_condition():
                self.executor()

        self.assertTrue(mocked_handler.called)
        self.assertEqual(mocked_handler.call_count, 1)
        _, call_args = mocked_handler.call_args
        settings_action = self.handler_settings['actions'][1]  # FAKE_ACTION
        self.assertEqual(call_args.get('instance'), self.userrequest)
        self.assertEqual(call_args.get('user'),
                         settings_action['kwargs']['user'])
        self.assertIsNotNone(call_args.get('signal'))  # Not predictable
