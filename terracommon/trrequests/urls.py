from rest_framework import routers

from .views import CommentViewSet, OrganizationViewSet, RequestViewSet

router = routers.SimpleRouter()

router.register(r'userrequest', RequestViewSet, base_name='request')
router.register(r'organization', OrganizationViewSet, base_name='organization')
router.register(r'request/(?P<request_pk>\d+)/comment',
                CommentViewSet, base_name='comment')

urlpatterns = router.urls
