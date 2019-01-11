from rest_framework import routers

from .views import DocumentTemplateViewSets

app_name = 'document_generator'

router = routers.SimpleRouter()

router.register(r'document-template',
                DocumentTemplateViewSets,
                base_name='document')

urlpatterns = router.urls
