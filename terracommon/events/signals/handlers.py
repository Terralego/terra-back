import types

from django.conf import settings
from django.core.mail import send_mail
from django.utils.functional import cached_property
from simpleeval import EvalWithCompoundTypes, simple_eval

from terracommon.terra.models import TerraUser

from . import funcs


class AbstractHandler(object):
    settings = {
        'CONDITION': True,
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
            self.settings['CONDITION'],
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
    SUBJECT_TPL and BODY_TPL are formatted with python .format() method.
    """

    settings = {
        'CONDITION': 'True',
        'FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'RECIPIENT_EMAILS': "[user['email'], ]",
        'SUBJECT_TPL': "Hello world {user[email]}",
        'BODY_TPL': "Dear, your properties {user[properties]}"
    }

    def __call__(self):
        s = EvalWithCompoundTypes(
            names=self.vars,
            functions=self.functions
            )
        recipients = s.eval(self.settings['RECIPIENT_EMAILS'])

        for recipient in recipients:
            recipient_data = self._get_recipient_data(recipient)

            subject = self.settings['SUBJECT_TPL'].format(
                recipient=recipient_data,
                **self.vars,)
            body = self.settings['BODY_TPL'].format(
                recipient=recipient_data,
                **self.vars,)

            send_mail(
                subject,
                body,
                self.settings['FROM_EMAIL'],
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
