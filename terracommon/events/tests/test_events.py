from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.events.models import EventHandler
from terracommon.events.signals import event
from terracommon.events.signals.handlers import UpdateRequestExpiryDateHandler
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


class ExpiryDateHandlerTestCase(TestCase):

    def setUp(self):
        self.userrequest = UserRequestFactory()

    def test_handler(self):
        daysdelta = '20'

        args = {
            'instance': self.userrequest,
            'user': self.userrequest.owner,
        }

        executor = UpdateRequestExpiryDateHandler(
            'USERREQUEST_CREATED',
            {'daysdelta': daysdelta},
            **args)

        if executor.valid_condition():
            executor()

        self.userrequest.refresh_from_db()

        self.assertEqual(
            self.userrequest.expiry,
            date.today() + timedelta(days=int(daysdelta))
            )
