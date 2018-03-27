from rest_framework import routers

from .views import RequestViewSet

urlpatterns = []

router = routers.SimpleRouter()

router.register(r'request', RequestViewSet, base_name='request')

urlpatterns += router.urls
