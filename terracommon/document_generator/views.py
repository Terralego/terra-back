from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from terracommon.terra.helpers import get_media_response
from terracommon.trrequests.models import UserRequest

from .helpers import CachedDocument, DocumentGenerator
from .models import DocumentTemplate, DownloadableDocument


class DocumentTemplateViewSets(viewsets.ViewSet):
    """
    pdf_creator:
    Create a new pdf document from a template link to a user request.
    """
    permission_classes = (IsAuthenticated, )

    @detail_route(methods=['POST'],
                  url_name='pdf',
                  url_path='pdf/(?P<request_pk>[^/.]+)')
    def pdf_creator(self, request, pk=None, request_pk=None):
        """ Insert data from user request into a template & convert it to pdf

        <pk>: template's id
        <request_pk>: user request's id
        """

        userrequest = get_object_or_404(UserRequest, pk=request_pk)
        mytemplate = get_object_or_404(DocumentTemplate, pk=pk)

        if not (request.user.is_superuser or
                request.user.has_perm('trrequests.can_download_all_pdf')):
            try:
                userrequest_type = ContentType.objects.get_for_model(
                                                            userrequest)
                DownloadableDocument.objects.get(
                    user=request.user,
                    document=mytemplate,
                    content_type=userrequest_type,
                    object_id=userrequest.pk
                )
            except DownloadableDocument.DoesNotExist:
                return Response(status=status.HTTP_403_FORBIDDEN)

        mytemplate_path = str(mytemplate.documenttemplate)
        mytemplate_name = str(mytemplate.name)

        # Cache_name is of the form
        # <templatepath>/<templatename>_<pk>.pdf
        userrequest_clsname = userrequest.__class__.__name__
        cache_name = (f'{mytemplate_path}{mytemplate_name}_'
                      f'{userrequest_clsname}_'
                      f'{userrequest.pk}.pdf')
        template_cache = CachedDocument(cache_name)

        if not template_cache.is_cached():
            pdf_generator = DocumentGenerator(mytemplate_path)
            pdf = pdf_generator.get_pdf(userrequest.properties)
            template_cache.create_cache(pdf, 'wb')

        response = get_media_response(request,
                                      template_cache.path,
                                      headers={
                                        'Content-Type': 'application/pdf',
                                        'Content-disposition': (
                                            'attachment;'
                                            f'filename={cache_name}')
                                        })
        return response
