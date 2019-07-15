from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'tropp'

router = SimpleRouter()

router.register(r'viewpoints', views.ViewpointViewSet, base_name='viewpoint')
router.register(r'campaigns', views.CampaignViewSet, base_name='campaign')
router.register(r'pictures', views.PictureViewSet, base_name='picture')

urlpatterns = router.urls

urlpatterns += [
    path(
        'viewpoints/<int:pk>/pdf',
        views.ViewpointPdf.as_view(),
        name='viewpoint-pdf',
    ),
    path(
        'viewpoints/<int:pk>/zip-pictures',
        views.ViewpointZipPictures.as_view(),
        name='viewpoint-zip',
    ),
]
