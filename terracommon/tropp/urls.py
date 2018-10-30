from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()

router.register(r'viewpoint', views.ViewpointViewSet, base_name='viewpoint')
router.register(r'campaign', views.CampaignViewSet, base_name='campaign')
router.register(r'picture', views.PictureViewSet, base_name='picture')
router.register(r'document', views.DocumentViewSet, base_name='document')
router.register(r'theme', views.ThemeViewSet, base_name='theme')

urlpatterns = router.urls
