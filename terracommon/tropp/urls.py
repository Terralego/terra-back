from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'tropp'

router = SimpleRouter()

router.register(r'viewpoints', views.ViewpointViewSet, base_name='viewpoints')
router.register(r'campaigns', views.CampaignViewSet, base_name='campaigns')
router.register(r'pictures', views.PictureViewSet, base_name='pictures')
router.register(r'documents', views.DocumentViewSet, base_name='documents')
router.register(r'themes', views.ThemeViewSet, base_name='themes')

urlpatterns = router.urls

urlpatterns += [
    path(
        'viewpoint_advanced_search/',
        views.ViewpointAdvancedSearchOptions.as_view(),
        name='viewpoints-search-options'
    ),
]
