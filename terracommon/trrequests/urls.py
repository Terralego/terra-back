from rest_framework import routers

from .views import CommentViewSet, RequestViewSet

app_name = 'trrequests'

router = routers.SimpleRouter()

router.register(r'userrequest', RequestViewSet, basename='request')
router.register(r'userrequest/(?P<request_pk>\d+)/comment',
                CommentViewSet, basename='comment')

urlpatterns = router.urls
