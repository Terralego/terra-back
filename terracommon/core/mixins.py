from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import Http404
from django.utils.functional import cached_property


class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field
    filtering.
    """
    def get_object(self):

        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends

        value = self.kwargs[self.lookup_field]
        for field in self.lookup_fields:
            try:
                obj = queryset.get(**{field: value})
            except (ObjectDoesNotExist, ValueError):
                continue
            else:
                self.check_object_permissions(self.request, obj)
                return obj
        raise Http404


class SerializerCurrentUserMixin(object):
    """
    Usefull mixin in serializers to get currently logged in user, in the
    current_user property
    """

    @cached_property
    def current_user(self):
        return (self.context['request'].user
                if 'request' in self.context else None)


class BaseUpdatableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
