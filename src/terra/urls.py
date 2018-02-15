from django.urls import path

from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import LayerViewSet, FeatureViewSet, FeatureRelationViewSet


schema_view = get_schema_view(
   openapi.Info(
      title="Terra PI",
      default_version='v1',
      description="The futur of Makina Corpus",
   ),
   validators=['flex', 'ssv'],
   public=True,
   permission_classes=(permissions.AllowAny, ),
)
urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=None), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=None), name='schema-redoc'),
]

router = routers.SimpleRouter()
router.register(r'layer', LayerViewSet)
router.register(r'feature', FeatureViewSet)
router.register(r'feature_relation', FeatureRelationViewSet)
urlpatterns += router.urls
