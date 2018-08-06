import types
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
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


class TimeDeltaHandler(AbstractHandler):
    '''Set the ```field``` element of the instance as a timedelta from today.
    It's possible to set a field content, as it's possible to set a property
    content.
    Available field from UserRequest are ```['expiry', 'properties', ]```
    '''

    settings = {
        'condition': 'True',
        'daysdelta': 0,
        'field': 'expiry',
    }

    def __call__(self):
        field_path = self.settings['field'].split('.')

        if field_path[0] not in ['expiry', 'properties']:
            return

        self._set_value(field_path, self.args['instance'])
        self.args['instance'].save()

    def _set_value(self, field_path, attr):
        if len(field_path) > 1:
            field_name = field_path.pop(0)

            modified_attr = getattr(attr, field_name, {})
            modified_attr = self._set_value(field_path, modified_attr)

            self._setattr(attr, field_name, modified_attr)

        else:
            self._setattr(attr, field_path.pop(),
                          str(date.today() + self._get_timedelta()))

        return attr

    def _setattr(self, attr, key, value):
        try:
            setattr(attr, key, value)
        except AttributeError:
            attr[key] = value

    def _get_timedelta(self):
        return timedelta(days=int(self.settings['daysdelta']))


class SetGroupHandler(AbstractHandler):
    settings = {
        'condition': 'True',
        'group': None,
        'userfield': None,
    }

    def __call__(self):
        group = Group.objects.get(name=self.settings['group'])
        self.args[self.settings['userfield']].groups.add(group)
