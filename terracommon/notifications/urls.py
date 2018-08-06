
from rest_framework import routers

from .views import NotificationViewSet

app_name = 'notifications'

router = routers.SimpleRouter()

router.register(r'notifications',
                NotificationViewSet,
                base_name='notifications')

urlpatterns = router.urls
