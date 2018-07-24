from django.core.cache import cache
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import detail_route

from terracommon.trrequests.models import UserRequest

from .helpers import DocumentGenerator
from .models import DocumentTemplate


class DocumentTemplateViewSets(viewsets.ViewSet):
    @detail_route(methods=['POST'],
                  url_name='pdf',
                  url_path='pdf/(?P<request_pk>[^/.]+)')
    def pdf_creator(self, request, pk=None, request_pk=None):
        userrequest = get_object_or_404(UserRequest, pk=request_pk)
        mytemplate = get_object_or_404(DocumentTemplate, pk=pk)

        mytemplate_path = str(mytemplate.template)
        mytemplate_name = str(mytemplate.name)

        pdf = cache.get(mytemplate_name)
        if not pdf:
            pdf_generator = DocumentGenerator(mytemplate_path)
            pdf = pdf_generator.get_pdf(userrequest.properties)
            cache.set(mytemplate_name, pdf)

        response = HttpResponse(pdf)
        response['Content-Type'] = 'application/pdf'
        response['Content-disposition'] = f'attachment; filename=macaron.pdf'
        return response
