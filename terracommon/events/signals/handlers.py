import types

from django.core.mail import send_mail
from simpleeval import EvalWithCompoundTypes, simple_eval

from . import funcs


class AbstractHandler(object):
    settings = {
        'condition': True,
    }

    def __init__(self, event, settings):
        self.event = event
        self.settings.update(settings)

    def is_callable(self, **kwargs):
        return simple_eval(
            self.settings.get('condition'),
            names=self.get_names(**kwargs)
            )

    def get_names(self, **kwargs):
        return {k: str(v) for k, v in kwargs.items()}

    def get_functions(self):
        return {
            f: getattr(funcs, f)
            for f in dir(funcs)
            if isinstance(getattr(funcs, f), types.FunctionType)
        }

    def __call__(self, **kwargs):
        raise NotImplementedError


class SendEmailHandler(AbstractHandler):
    """
    This handler send an email to the list of users returned by the «emails»
    interpreted settings.
    «subject_tpl» and «body_tpl» are formatted with python .format() method.
    """

    settings = {
        'condition': 'True',
        'from': 'terralego@terralego',
        'emails': "[user['email'], ]",
        'subject_tpl': "Hello world {user[email]}",
        'body_tpl': "Dear, your properties {user[properties]}"
    }

    def __call__(self, **kwargs):
        names = self.get_names(**kwargs)
        s = EvalWithCompoundTypes(
            names=names,
            functions=self.get_functions()
            )
        receivers = s.eval(self.settings.get('emails'))

        for receiver in receivers:
            subject = self.settings.get('subject_tpl').format(**names)
            body = self.settings.get('body_tpl').format(**names)
            send_mail(
                subject,
                body,
                self.settings.get('from'),
                [receiver, ],
                fail_silently=True,
                )

    def get_names(self, **kwargs):
        return {
            'user': {
                'email': kwargs.get('user').email,
                'properties': kwargs.get('user').properties
            },
        }
