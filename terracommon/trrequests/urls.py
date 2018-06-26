from rest_framework import routers

from .views import CommentViewSet, RequestViewSet, UploadFileViewSet

router = routers.SimpleRouter()

router.register(r'userrequest', RequestViewSet, base_name='request')
router.register(r'userrequest/(?P<request_pk>\d+)/comment',
                CommentViewSet, base_name='comment')
router.register(
    r'userrequest/(?P<request_pk>\d+)/comment/(?P<comment_pk>\d+)/file',
    UploadFileViewSet, base_name='file')

urlpatterns = router.urls
