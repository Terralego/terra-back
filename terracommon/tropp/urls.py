from rest_framework.routers import SimpleRouter

from .views import (CampaignViewSet, DocumentViewSet, LayerViewSet,
                    ObservationPointViewSet, PictureViewSet, ThemeViewSet)

router = SimpleRouter()

router.register(
    r'observation-points',
    ObservationPointViewSet,
    base_name='observation-point',
)
router.register(r'campaigns', CampaignViewSet, base_name='campaign')
router.register(r'pictures', PictureViewSet, base_name='picture')
router.register(r'documents', DocumentViewSet, base_name='document')
router.register(r'themes', ThemeViewSet, base_name='theme')
router.register(r'layers', LayerViewSet, base_name='layer')

urlpatterns = router.urls
