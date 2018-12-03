from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'tropp'

router = SimpleRouter()

router.register(r'viewpoints', views.ViewpointViewSet, base_name='viewpoint')
router.register(r'campaigns', views.CampaignViewSet, base_name='campaign')
router.register(r'pictures', views.PictureViewSet, base_name='picture')
router.register(r'documents', views.DocumentViewSet, base_name='document')

urlpatterns = router.urls

urlpatterns += [
    path(
        'viewpoint_advanced_search/',
        views.ViewpointAdvancedSearchOptions.as_view(),
        name='viewpoint-search-options'
    ),
]
