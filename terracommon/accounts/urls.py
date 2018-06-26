from rest_framework import routers

from .views import UserViewSet

router = routers.SimpleRouter()

router.register(r'accounts', UserViewSet, base_name='accounts')

urlpatterns = router.urls
