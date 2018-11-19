from rest_framework import filters


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
    Filter viewpoint picture with photographer's email
    """

    def filter_queryset(self, request, queryset, view):
        photographer = request.GET.get('photographer', None)

        if photographer is not None:
            queryset = queryset.filter(
                pictures__owner__email=photographer,
            )
        return queryset
