import os
from datetime import date

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from jinja2 import TemplateSyntaxError
from requests.exceptions import ConnectionError, HTTPError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from terracommon.accounts.permissions import TokenBasedPermission
from terracommon.document_generator.helpers import get_media_response
from terracommon.trrequests.models import UserRequest

from .helpers import DocumentGenerator
from .models import DocumentTemplate, DownloadableDocument
from .serializers import DocumentTemplateSerializer


class DocumentTemplateViewSets(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.none()
    serializer_class = DocumentTemplateSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        if self.request.user.has_module_perms('document_generator'):
            return DocumentTemplate.objects.all()
        return DocumentTemplate.objects.none()

    def create(self, request, *args, **kwargs):
        if not request.user.has_perm(
                'document_generator.can_upload_template'):
            raise PermissionDenied

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.has_perm(
                'document_generator.can_update_template'):
            raise PermissionDenied

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.has_perm(
                'document_generator.can_delete_template'):
            raise PermissionDenied

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'], permission_classes=(TokenBasedPermission,))
    def file(self, request, pk=None):
        document = self.get_object().documenttemplate
        if not document:
            raise Http404('Attachment does not exist')

        response = get_media_response(
            request, document,
            headers={
                'Content-Disposition': (
                    'attachment;'
                    f' filename={document.name}'),
            }
        )

        return response

    @action(detail=True,
            methods=['get'],
            url_name='pdf',
            url_path='pdf/(?P<request_pk>[^/.]+)',
            permission_classes=(TokenBasedPermission,))
    def pdf_creator(self, request, pk=None, request_pk=None):
        """ Insert data from user request into a template & convert it to pdf

        <pk>: template's id
        <request_pk>: user request's id
        """

        userrequest = get_object_or_404(UserRequest, pk=request_pk)
        template = get_object_or_404(DocumentTemplate, pk=pk)

        userrequest_type = ContentType.objects.get_for_model(
                                                        userrequest)
        downloadable_properties = {
            'document': template,
            'content_type': userrequest_type,
            'object_id': userrequest.pk,
        }
        if not ((request.user.is_superuser
                 or request.user.has_perm('trrequests.can_download_all_pdf')
                or request.user.downloadabledocument_set.filter(
                    **downloadable_properties).exists())):
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            pdf_generator = DocumentGenerator(
                DownloadableDocument.objects.get(**downloadable_properties)
            )
            pdf_path = pdf_generator.get_pdf()
        except FileNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except (ConnectionError, HTTPError):
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except TemplateSyntaxError:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data='malformed template'
            )
        else:
            pdf_url = os.path.join(settings.MEDIA_URL, pdf_path)

            filename = f'document_{date.today().__str__()}.pdf'
            response = get_media_response(
                request,
                {'path': pdf_path, 'url': pdf_url},
                headers={
                    'Content-Type': 'application/pdf',
                    'Content-disposition': f'attachment;filename={filename}'
                }
            )
            return response
