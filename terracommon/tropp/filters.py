from pprint import pformat

import coreapi
import coreschema
from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import Q
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from terracommon.core.settings import STATES


class CampaignFilterBackend(filters.BaseFilterBackend):
    """
    Filters for campaigns
    """

    def get_schema_fields(self, view):
        super().get_schema_fields(view)
        choices = {
            STATES.DRAFT: 'Incomplete metadata',
            STATES.SUBMITTED: 'Pending validation',
            STATES.REFUSED: 'Refused',
            STATES.ACCEPTED: 'Validated',
        }
        return [
            coreapi.Field(
                name='status',
                required=False,
                location='query',
                schema=coreschema.Boolean(
                    title="Campaign status",
                    description="0 for closed campaign, 1 for ongoing campaign"
                ),
            ),
            coreapi.Field(
                name='picture_status',
                required=False,
                location='query',
                schema=coreschema.Enum(
                    choices,
                    description=str(pformat(choices)),
                    title="Picture status",
                )
            )
        ]

    def filter_queryset(self, request, queryset, view):
        status = request.GET.get('status', None)
        if status is not None:
            try:
                status = bool(int(status))
            except ValueError:
                raise ValidationError
            if status:
                queryset = queryset.filter(
                    viewpoints__pictures__state=STATES.ACCEPTED
                )
            else:
                queryset = queryset.exclude(
                    Q(viewpoints__pictures__state=STATES.ACCEPTED)
                )

        picture_status = request.GET.get('picture_status', None)
        if picture_status is not None:
            try:
                picture_status = int(picture_status)
                assert picture_status in STATES.CHOICES_DICT
            except (AssertionError, ValueError):
                raise ValidationError
            queryset = queryset.filter(
                viewpoints__pictures__state=picture_status
            )

        return queryset


class JsonFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            search_key = f'properties__{field["json_key"]}'
            if field['type'] == 'many':
                search_item = request.GET.getlist(f'{search_key}[]')
            else:
                search_item = request.GET.get(search_key)
            if search_item:
                if field['type'] == 'text':
                    # Full text search
                    queryset = queryset.annotate(**{
                        key: KeyTextTransform(field['json_key'], 'properties')
                    }).filter(**{f'{key}__icontains': search_item})
                else:
                    # Search on element
                    queryset = queryset.filter(**{
                        f'{search_key}__contains': search_item
                    })
        return queryset

    def get_schema_fields(self, view):
        fields = []
        for key, field in settings.TROPP_SEARCHABLE_PROPERTIES.items():
            if field['type'] == 'many':
                klass = coreschema.Array
            else:
                klass = coreschema.String
            description = f"{key.capitalize()} property ({field['type']})"
            fields.append(
                coreapi.Field(
                    name=f'properties__{field["json_key"]}',
                    required=False,
                    location='query',
                    schema=klass(
                        title=f"{key.capitalize()} property",
                        description=description,
                    ),
                )
            )
        return super().get_schema_fields(view)
