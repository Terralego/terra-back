from rest_framework import routers

from .views import LayerViewSet, FeatureViewSet


router = routers.SimpleRouter()
router.register(r'layers', LayerViewSet)
router.register(r'features', FeatureViewSet)
urlpatterns = router.urls
