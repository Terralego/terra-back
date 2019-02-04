import logging
import types
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.mail import send_mail
from django.db.models import Model
from django.forms.models import model_to_dict
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from simpleeval import EvalWithCompoundTypes, simple_eval

from terracommon.events.signals import event

from . import funcs

logger = logging.getLogger(__name__)


class AbstractHandler(object):

    default_settings = {
        'condition': 'True',
    }
    default_args = {
        'instance': None,
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
        self.handler_settings = settings or {}
        self.args = {**self.default_args, **kwargs}

    @property
    def settings(self):
        return {**self.default_settings, **self.handler_settings}

    def valid_condition(self):
        return simple_eval(
            self.settings['condition'],
            names=self.vars,
            functions=self.functions,
            )

    @cached_property
    def vars(self):
        attrs = {k: str(v) for k, v in self.args.items()}
        attrs.update({
            'settings': self.settings,
            'event': self.event,
            'instance': self.serialized_instance,
            'front_url': settings.FRONT_URL,
            'hostname': settings.HOSTNAME,
        })

        return attrs

    @cached_property
    def serialized_instance(self):
        instance = self.args.get('instance')
        if isinstance(instance, Model):
            return model_to_dict(instance)
        try:
            return vars(instance)
        except TypeError:
            return {}

    @cached_property
    def functions(self):
        functions = {
            f: getattr(funcs, f)
            for f in dir(funcs)
            if isinstance(getattr(funcs, f), types.FunctionType)
        }

        functions.update({
            'min': min,
            'max': max,
            'any': any,
            'all': all,
            'sum': sum,
        })

        return functions

    def __call__(self):
        raise NotImplementedError


class SendEmailHandler(AbstractHandler):
    """
    This handler send an email to the list of users returned by the «emails»
    interpreted settings.
    subject_tpl and body_tpl are formatted with python .format() method.
    """

    default_settings = {
        'condition': 'True',
        'from_email': settings.DEFAULT_FROM_EMAIL,
        'recipients': "[user['email'], ]",
        'subject_tpl': "Hello world {user[email]}",
        'body_tpl': "Dear, your properties {user[properties]}"
    }

    def __call__(self):
        s = EvalWithCompoundTypes(
            names=self.vars,
            functions=self.functions
            )
        recipients = s.eval(self.settings['recipients'])

        for recipient in recipients:
            recipient_data = self._get_recipient_data(recipient)

            subject = self.settings['subject_tpl'].format(
                recipient=recipient_data,
                **self.vars,)
            body = self.settings['body_tpl'].format(
                recipient=recipient_data,
                **self.vars,)
            to_email = getattr(recipient_data, 'email', recipient)

            if to_email:
                send_mail(
                    subject,
                    body,
                    self.settings['from_email'],
                    [to_email, ],
                    fail_silently=True,
                    )
            else:
                logger.error('No destination e-mail could be found for %s',
                             recipient)

    @cached_property
    def vars(self):
        vars = super().vars
        if isinstance(self.args['user'], get_user_model()):
            vars.update({
                'user': {
                    'email': self.args['user'].email,
                    'properties': self.args['user'].properties,
                },
            })
        return vars

    def _get_recipient_data(self, o):
        if isinstance(o, get_user_model()):
            return o
        try:
            user = get_user_model().objects.get(email=o)
            return {
                'email': user.email,
                'properties': user.properties,
            }
        except get_user_model().DoesNotExist:
            return None


class TimeDeltaHandler(AbstractHandler):
    '''Set the ```field``` element of the instance as a timedelta from today.
    It's possible to set a field content, as it's possible to set a property
    content.
    Available field from UserRequest are ```['expiry', 'properties', ]```
    '''

    default_settings = {
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


class SendNotificationHandler(AbstractHandler):

    default_settings = {
        'condition': 'True',
        'level': 'info',
        'message': "New notifications received",
        'event_code': 'default_notification',
    }

    def __call__(self):
        message = self.settings['message'].format(**self.vars)
        uuid = (self.args['instance'].uuid
                if hasattr(self.args['instance'], 'uuid') else None)

        self.args['user'].notifications.create(
            level=self.settings.get('level'),
            message=message,
            event_code=self.settings.get('event_code'),
            identifier=self.args['instance'].pk,
            uuid=uuid,
        )


class SetGroupHandler(AbstractHandler):
    default_settings = {
        'condition': 'True',
        'group': None,
        'userfield': None,
    }

    def __call__(self):
        group = Group.objects.get(name=self.settings['group'])
        self.args[self.settings['userfield']].groups.add(group)


class ModelValueHandler(AbstractHandler):
    """
    Retrieves model records that validates the query.
    The query values are evaluated before being passed to the ORM.
    Triggers actions for each recovered record.
    """

    default_settings = {
        'condition': 'True',
        'model': None,
        'query': {},
        'actions': None,
    }

    def __call__(self):
        instances = self._get_queryset().all()
        actions = self.settings['actions']
        for instance in instances:
            for action in actions:
                kwargs = {'user': AnonymousUser()}
                kwargs.update(**action.get('kwargs', {}))
                kwargs.update({'action': action['action'],
                               'instance': instance, })
                event.send(self.__class__, **kwargs)

    def _get_queryset(self):
        model = import_string(self.settings['model'])
        kwargs = {
            k: simple_eval(v,
                           names=self.vars,
                           functions=self.functions, )
            for k, v in self.settings['query'].items()
        }
        return model.objects.filter(**kwargs)

    @cached_property
    def serialized_instance(self):
        return None

    @cached_property
    def functions(self):
        functions = super().functions
        functions.update({
            'date': date,
            'timedelta': timedelta,
        })
        return functions
