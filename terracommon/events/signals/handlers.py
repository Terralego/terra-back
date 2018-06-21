from django.core.mail import send_mail
from simpleeval import EvalWithCompoundTypes, simple_eval


class AbstractHandler(object):
    settings = {
        'condition': True,
    }

    def __init__(self, event, settings):
        self.event = event
        self.settings.update(settings)

    def is_callable(self):
        return simple_eval(self.settings.get('condition'))

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def _clean_kwargs(self, **kwargs):
        # TODO Clean kwargs to have a dict of values, no objects
        return kwargs


class SendEmailHandler(AbstractHandler):
    """
    This handler send an email to the list of users returned by the «emails»
    interpreted settings.
    «subject_tpl» and «body_tpl» are formatted with python .format() method.
    """

    settings = {
        'condition': True,
        'from': 'terralego@terralego',
        'emails': '[user.email, ]',
        'subject_tpl': 'Hello world {user.email}',
        'body_tpl': 'Dear, your properties {user.properties} '
    }

    def __call__(self, **kwargs):
        args = self._clean_kwargs(**kwargs)
        s = EvalWithCompoundTypes(names=args)

        receivers = s.eval(self.settings.get('emails'))

        for receiver in receivers:
            subject = self.settings.get('subject_tpl').format(**args)
            body = self.settings.get('body_tpl').format(**args)
            send_mail(
                subject,
                body,
                self.settings.get('from'),
                [receiver, ],
                fail_silently=True,
                )
