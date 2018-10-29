from datetime import timedelta

from django.utils.dateparse import parse_datetime

from terracommon.datastore.models import DataStore


def timedelta_filter(date_value, delta_days=0):
    """ custom filter that will add a positive or negative value, timedelta
        to the day of a date in string format """

    current_date = parse_datetime(date_value)
    return current_date - timedelta(days=delta_days)


def translate_filter(data, datastorekey=''):
    """ Custom filter that will return the translated data
        from datastore correspondence table """

    if not datastorekey:
        return data
    correspondences = DataStore.objects.get(key=datastorekey)
    return correspondences.value[data]