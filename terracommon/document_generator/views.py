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
        myodt = get_object_or_404(DocumentTemplate, pk=pk)

        myodt_path = str(myodt.template)

        pdf_generator = DocumentGenerator(myodt_path)
        pdf = pdf_generator.get_pdf(userrequest.properties)

        response = HttpResponse(pdf)
        response['Content-Type'] = 'application/pdf'
        response['Content-disposition'] = f'attachment; filename=macaron.pdf'
        return response
