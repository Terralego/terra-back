import base64
from datetime import timedelta
from tempfile import NamedTemporaryFile

from django.utils.dateparse import parse_datetime
from docx.shared import Mm
from docxtpl import InlineImage
from jinja2 import contextfilter

from terracommon.datastore.models import DataStore


def timedelta_filter(date_value, **kwargs):
    """ custom filter that will add a positive or negative value, timedelta
        to the day of a date in string format """

    current_date = parse_datetime(date_value)
    return (current_date - timedelta(**kwargs))


def translate_filter(value, datastorekey=''):
    """ Custom filter that will return the translated data
        from datastore correspondence table """

    if not datastorekey:
        return value
    correspondences = DataStore.objects.get(key=datastorekey)
    return correspondences.value.get(value, value)


def todate_filter(value):
    return parse_datetime(value).date()


@contextfilter
def b64_to_inlineimage(context, value):
    b64str = value.split(',', 1)[1]
    decoded = base64.b64decode(b64str)
    tmp_f = NamedTemporaryFile(mode='wb', dir=context['tmpdir'], delete=False)
    tmp_f.write(decoded)
    tmp_f.seek(0)
    return InlineImage(context['tpl'], tmp_f.name, width=Mm(40))
