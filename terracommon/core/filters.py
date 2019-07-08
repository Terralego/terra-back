import coreapi
import coreschema
from django.db.models.expressions import OrderBy, RawSQL
from django.utils.dateparse import parse_date
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from url_filter.integrations.drf import DjangoFilterBackend


class JSONFieldOrderingFilter(OrderingFilter):

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        if not ordering:
            ordering = []

        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            for field in fields:
                json_nested = field.split('__')
                model_field = json_nested.pop(0)
                descending = False

                if (model_field in ordering or
                    not self.remove_invalid_fields(queryset,
                                                   [model_field, ],
                                                   view,
                                                   request)):
                    # The model_field must be an authorized field
                    continue

                if model_field.startswith('-'):
                    descending = True
                    model_field = model_field[1:]

                tpl = model_field + ''.join(
                    ['->>%s' for x in range(len(json_nested))])

                ordering.append(
                    OrderBy(RawSQL('lower({})'.format(tpl), json_nested),
                            descending=descending))

        if not ordering:
            ordering = None

        return ordering


class DateFilterBackend(filters.BaseFilterBackend):
    """
    Filter from date to date.

    You must specify which field to search on with `date_search_field` in
    your view.

    Example:
       date_search_field = 'created_at'
    """

    def get_schema_fields(self, view):
        super().get_schema_fields(view)
        search_field = getattr(view, 'date_search_field', None)
        return [
            coreapi.Field(
                name='date_from',
                required=False,
                location='query',
                schema=coreschema.String(
                    title="Begin date",
                    description=f"Begin date for {search_field}",
                    pattern='[0-9]{4}-[0-9]{2}-[0-9]{2}',
                ),
            ),
            coreapi.Field(
                name='date_to',
                required=False,
                location='query',
                schema=coreschema.String(
                    title="End date",
                    description=f"End date for {search_field}",
                    pattern='[0-9]{4}-[0-9]{2}-[0-9]{2}',
                ),
            ),
        ]

    def filter_queryset(self, request, queryset, view):
        search_field = getattr(view, 'date_search_field', None)
        date_from = self.parse_date(request.GET.get('date_from', None))
        date_to = self.parse_date(request.GET.get('date_to', None))

        if date_from and date_to and date_from > date_to:
            raise ValidationError

        if date_from is not None and date_to is not None:
            queryset = queryset.filter(
                **{f'{search_field}__range': (date_from, date_to)}
            )
        elif date_from is not None:
            queryset = queryset.filter(**{f'{search_field}__gte': date_from})
        elif date_to is not None:
            queryset = queryset.filter(**{f'{search_field}__lte': date_to})

        return queryset

    @staticmethod
    def parse_date(value):
        """
        Shamelessly taken from DateField.to_python

        :param value:
        :return:
        """
        if value is None:
            return value

        try:
            parsed = parse_date(value)
            if parsed is not None:
                return parsed
        except ValueError:
            raise ValidationError

        raise ValidationError


class SchemaAwareDjangoFilterBackend(DjangoFilterBackend):
    def get_schema_fields(self, view):
        """
        Get coreapi filter definitions

        Returns all schemas defined in filter_fields_schema attribute.
        """
        super().get_schema_fields(view)
        return getattr(view, 'filter_fields_schema', [])
