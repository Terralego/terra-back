from .views import OrganizationViewSet, RequestViewSet, CommentViewSet

from rest_framework import routers

router = routers.SimpleRouter()

router.register(r'request', RequestViewSet, base_name='request')
router.register(r'organization', OrganizationViewSet, base_name='organization')
router.register(r'request/(?P<request_pk>\d+)/comment', CommentViewSet, base_name='comment')

urlpatterns = router.urls
