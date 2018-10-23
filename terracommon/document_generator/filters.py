from datetime import timedelta

from django.utils.dateparse import parse_datetime


def timedelta_filter(date_value, delta_days=0):
    """ custom filter that will add a positive or negative value, timedelta
        to the day of a date in string format """

    current_date = parse_datetime(date_value)
    return current_date - timedelta(days=delta_days)
