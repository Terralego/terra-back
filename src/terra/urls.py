from rest_framework import routers

from .views import LayerViewSet, FeatureViewSet, FeatureRelationViewSet


router = routers.SimpleRouter()
router.register(r'layer', LayerViewSet)
router.register(r'feature', FeatureViewSet)
router.register(r'feature_relation', FeatureRelationViewSet)
urlpatterns = router.urls
