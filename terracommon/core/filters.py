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

                if not self.remove_invalid_fields(queryset,
                                                  [model_field, ],
                                                  view,
                                                  request):
                    # The model_field must be an authorized field
                    continue

                tpl = model_field + ''.join(
                    ['->%s' for x in range(len(json_nested))])

                if not ordering:
                    ordering = []

                ordering.append(OrderBy(RawSQL(tpl, json_nested)))

        return ordering
