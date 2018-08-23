from datetime import date, timedelta
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.forms.models import model_to_dict
from django.test import TestCase, override_settings

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.events.models import EventHandler
from terracommon.trrequests.tests.factories import UserRequestFactory


class ExecuteActionTestCase(TestCase):

    def setUp(self):
        self.handler_path = ('terracommon.events.signals'
                             '.handlers.AbstractHandler')
        EventHandler.objects.create(
            action='FAKE_ACTION',
            handler=self.handler_path,
        )
        EventHandler.objects.create(
            action='OTHER_FAKE_ACTION',
            handler=self.handler_path,
        )

    def test_command_launch(self):
        with patch(self.handler_path) as mocked_handler:
            call_command('execute_action',
                         '--action=FAKE_ACTION',
                         '--instance=myInstance',
                         '--user=myUser',
                         '--kwargs=foo:bar')
        mocked_handler.assert_called_once()
        _, call_args = mocked_handler.call_args
        self.assertEqual(call_args['instance'], 'myInstance')
        self.assertEqual(call_args['user'], 'myUser')
        self.assertEqual(call_args.get('foo'), 'bar')

    def test_command_launch_minimal_arguments(self):
        with patch(self.handler_path) as mocked_handler:
            call_command('execute_action',
                         '--action=FAKE_ACTION')
        mocked_handler.assert_called_once()
        _, call_args = mocked_handler.call_args
        self.assertEqual(call_args['instance'], None)
        self.assertEqual(call_args['user'], None)

    def test_command_launch_with_args_only(self):
        with patch(self.handler_path) as mocked_handler:
            call_command('execute_action',
                         '--kwargs=action:FAKE_ACTION')
        mocked_handler.assert_called_once()
        _, call_args = mocked_handler.call_args
        self.assertEqual(call_args['instance'], None)
        self.assertEqual(call_args['user'], None)

    def test_priority_of_arguments(self):
        with patch(self.handler_path) as mocked_handler:
            call_command('execute_action',
                         '--action=FAKE_ACTION',
                         '--user=user1',
                         '--kwargs=user:user2')
        mocked_handler.assert_called_once()
        _, call_args = mocked_handler.call_args
        self.assertEqual(call_args['user'], 'user1')

    def test_command_raise_exception_when_action_is_missing(self):
        with self.assertRaises(TypeError):
            call_command('execute_action',
                         '--kwargs=foo:bar')

    def test_command_raise_exception_with_incorrectly_formatted_kwargs(self):
        with self.assertRaises(ValueError):
            call_command('execute_action',
                         '--kwargs=lorem:ipsum:dolor')

    @override_settings(EMAIL_BACKEND=('django.core.mail.backends'
                                      '.locmem.EmailBackend'))
    def test_integration_with_SendEmailHandler(self):
        userrequests = []
        for i in range(0, 3):
            userrequests.append(
                UserRequestFactory(
                    expiry=date.today() + timedelta(days=i+1),
                )
            )
            userrequests[-1].reviewers.set([
                TerraUserFactory(email=f'reviewer{i*2+1}@makina-corpus.com'),
                TerraUserFactory(email=f'reviewer{i*2+2}@makina-corpus.com')
            ])

        signals = [
            {
                'action': 'EVERY_DAY',
                'handler': ('terracommon.events.signals.handlers'
                            '.ModelValueHandler'),
                'settings': {
                    'model': 'terracommon.trrequests.models.UserRequest',
                    'query': {
                        'expiry': 'date.today() + timedelta(days=2)',
                    },
                    'actions': [
                        {'action': 'USERREQUEST_WILL_EXPIRE_SOON', },
                    ]
                }
            }, {
                'action': 'USERREQUEST_WILL_EXPIRE_SOON',
                'handler': ('terracommon.events.signals.handlers'
                            '.SendEmailHandler'),
                'settings': {
                    'recipients': "instance['reviewers']",
                    'subject_tpl': "A user request will expire",
                    'body_tpl': ("The user request n°{instance[id]}"
                                 " will expire in 2 days")
                }
            }]
        for signal in signals:
            EventHandler.objects.create(**signal)

        self.assertEqual(len(mail.outbox), 0)

        call_command('execute_action',
                     '--action=EVERY_DAY')

        self.assertEqual(len(mail.outbox), 2)
        mail_signal = signals[1]
        userrequest = userrequests[1]
        for reviewer in userrequest.reviewers.all():
            reviewer_mails = list(
                filter(lambda m: reviewer.email in m.recipients(), mail.outbox)
            )
            self.assertEqual(len(reviewer_mails), 1)
            current_mail = reviewer_mails[0]
            format_kwargs = {
                'instance': model_to_dict(userrequest)
            }
            self.assertEqual(current_mail.subject,
                             mail_signal.get('settings', {})
                                        .get('subject_tpl', '')
                                        .format(**format_kwargs))
            self.assertEqual(current_mail.body,
                             mail_signal.get('settings', {})
                                        .get('body_tpl', '')
                                        .format(**format_kwargs))
