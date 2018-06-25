import types

from django.core.mail import send_mail
from django.utils.functional import cached_property
from simpleeval import EvalWithCompoundTypes, simple_eval

from . import funcs


class AbstractHandler(object):
    settings = {
        'CONDITION': True,
    }

    def __init__(self, event, settings, args):
        self.event = event
        self.settings.update(settings)
        self.args = args

    def is_callable(self, **kwargs):
        return simple_eval(
            self.settings.get('CONDITION'),
            names=self.vars,
            )

    @cached_property
    def vars(self):
        return {k: str(v) for k, v in self.args.items()}

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
        'FROM_EMAIL': 'terralego@terralego',
        'RECIPIENT_EMAILS': "[user['email'], ]",
        'SUBJECT_TPL': "Hello world {user[email]}",
        'BODY_TPL': "Dear, your properties {user[properties]}"
    }

    def __call__(self):
        s = EvalWithCompoundTypes(
            names=self.vars,
            functions=self.functions
            )
        receivers = s.eval(self.settings.get('RECIPIENT_EMAILS'))

        for receiver in receivers:
            subject = self.settings.get('SUBJECT_TPL').format(**self.vars)
            body = self.settings.get('BODY_TPL').format(**self.vars)
            send_mail(
                subject,
                body,
                self.settings.get('FROM_EMAIL'),
                [receiver, ],
                fail_silently=True,
                )

    @cached_property
    def vars(self):
        return {
            'user': {
                'email': self.args.get('user').email,
                'properties': self.args.get('user').properties
            },
        }
