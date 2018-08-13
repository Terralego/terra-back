from django.db.models.expressions import OrderBy, RawSQL
from rest_framework.filters import OrderingFilter


class JSONFieldOrderingFilter(OrderingFilter):

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            for field in fields:
                json_nested = field.split('__')
                model_field = json_nested.pop(0)
                descending = False

                if not ordering:
                    ordering = []

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
                    ['->%s' for x in range(len(json_nested))])

                ordering.append(
                    OrderBy(RawSQL(tpl, json_nested), descending=descending))

        return ordering
