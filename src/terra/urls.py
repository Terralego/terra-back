from rest_framework import routers

from .views import LayerViewSet, FeatureViewSet


router = routers.SimpleRouter()
router.register(r'layer', LayerViewSet)
router.register(r'feature', FeatureViewSet)
urlpatterns = router.urls
