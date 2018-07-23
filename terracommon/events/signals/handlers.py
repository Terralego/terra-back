import types
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils.functional import cached_property
from simpleeval import EvalWithCompoundTypes, simple_eval

from terracommon.accounts.models import TerraUser

from . import funcs


class AbstractHandler(object):
    settings = {
        'condition': 'True',
    }

    def __init__(self, event, settings, **kwargs):
        """
        :param event: Is the event name raised
        :param settings: Is a dict from settings of EventHandler model. It
                         override default Handler settings.
        :param **kwargs: Are all extra parameters provided by the event
                         sender. All those arguments are provided to all
                         eval or template.

        """
        self.event = event
        self.settings.update(settings)
        self.args = kwargs

    def valid_condition(self):
        return simple_eval(
            self.settings['condition'],
            names=self.vars,
            functions=self.functions,
            )

    @cached_property
    def vars(self):
        attrs = {
            'settings': self.settings,
            'event': self.event,
        }
        attrs.update({k: str(v) for k, v in self.args.items()})
        return attrs

    @cached_property
    def functions(self):
        return {
            f: getattr(funcs, f)
            for f in dir(funcs)
            if isinstance(getattr(funcs, f), types.FunctionType)
        }

    def __call__(self):
        raise NotImplementedError


class SendEmailHandler(AbstractHandler):
    """
    This handler send an email to the list of users returned by the «emails»
    interpreted settings.
    subject_tpl and body_tpl are formatted with python .format() method.
    """

    settings = {
        'condition': 'True',
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipient_emails': "[user['email'], ]",
        'subject_tpl': "Hello world {user[email]}",
        'body_tpl': "Dear, your properties {user[properties]}"
    }

    def __call__(self):
        s = EvalWithCompoundTypes(
            names=self.vars,
            functions=self.functions
            )
        recipients = s.eval(self.settings['recipient_emails'])

        for recipient in recipients:
            recipient_data = self._get_recipient_data(recipient)

            subject = self.settings['subject_tpl'].format(
                recipient=recipient_data,
                **self.vars,)
            body = self.settings['body_tpl'].format(
                recipient=recipient_data,
                **self.vars,)

            send_mail(
                subject,
                body,
                self.settings['from_email'],
                [recipient, ],
                fail_silently=True,
                )

    @cached_property
    def vars(self):
        return {
            'user': {
                'email': self.args['user'].email,
                'properties': self.args['user'].properties
            },
        }

    def _get_recipient_data(self, email):
        try:
            user = TerraUser.objects.get(email=email)
            return {
                'email': user.email,
                'properties': user.properties,
            }
        except TerraUser.DoesNotExist:
            return None


class UpdateRequestExpiryDateHandler(AbstractHandler):
    '''Update the expiration date of an userrequest, the userrequest
    must be provided in the instance event args.
    In the settings `daysdelta` is an integer day count relative  to the
    event type.
    '''

    settings = {
        'condition': 'True',
        'daysdelta': 0,
    }

    def __call__(self):
        self.args['instance'].expiry = datetime.today() + self._get_timedelta()
        self.args['instance'].save()

    def _get_timedelta(self):
        return timedelta(days=int(self.settings['daysdelta']))
