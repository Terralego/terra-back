from rest_framework import routers

from .views import CommentViewSet, RequestViewSet

app_name = 'trrequests'

router = routers.SimpleRouter()

router.register(r'userrequest', RequestViewSet, base_name='request')
router.register(r'userrequest/(?P<request_pk>\d+)/comment',
                CommentViewSet, base_name='comment')

urlpatterns = router.urls
