from .views import OrganizationViewSet, RequestViewSet

from rest_framework import routers

router = routers.SimpleRouter()

router.register(r'request', RequestViewSet, base_name='request')
router.register(r'organization', OrganizationViewSet, base_name='organization')

urlpatterns = router.urls
