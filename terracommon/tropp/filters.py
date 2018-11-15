from rest_framework import filters


class PictureDateFilterBackend(filters.BaseFilterBackend):
    """
    Filter viewpoint pictures from date to date.
    """
    def filter_queryset(self, request, queryset, view):
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)

        if date_from is not None and date_to is not None:
            queryset = queryset.filter(
                pictures__date__range=(date_from, date_to),
            )
        return queryset


class PictureIdFilterBackend(filters.BaseFilterBackend):
    """
    Filter viewpoint pictures id.
    """
    def filter_queryset(self, request, queryset, view):
        picture_id = request.GET.get('picture_id', None)

        if picture_id is not None:
            queryset = queryset.filter(
                pictures__id=picture_id,
            )
        return queryset


class PhotographerFilterBackend(filters.BaseFilterBackend):
    """
    Filter photographers
    """
    def filter_queryset(self, request, queryset, view):
        picture_id = request.GET.get('picture_id', None)

        if picture_id is not None:
            queryset = queryset.filter(
                pictures__id=picture_id,
            )
        return queryset
