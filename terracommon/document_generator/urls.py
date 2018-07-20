from rest_framework import routers

from .views import OdtViewSets

router = routers.SimpleRouter()

router.register(r'odtfile', OdtViewSets, base_name='odtfile')

urlpatterns = router.urls
