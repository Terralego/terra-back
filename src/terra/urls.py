from rest_framework import routers

from .views import LayerViewSet


router = routers.SimpleRouter()
router.register(r'layers', LayerViewSet)
urlpatterns = router.urls
