from django.http.response import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import detail_route

from terracommon.trrequests.models import UserRequest

from .helpers import DocumentGenerator
from .models import DocumentTemplate


class DocumentTemplateViewSets(viewsets.ViewSet):
    @detail_route(methods=['POST'],
                  url_name='pdf-creator',
                  url_path='pdf_creator/(?P<request_pk>[^/.]+)')
    def pdf_creator(self, request, pk=None, request_pk=None):
        userrequest = UserRequest.objects.get(pk=request_pk)

        myodt = DocumentTemplate.objects.get(pk=pk)
        myodt_path = str(myodt.template)

        pdf_generator = DocumentGenerator(myodt_path)
        pdf = pdf_generator.get_pdf(userrequest.properties)

        response = HttpResponse(pdf)
        response['Content-Type'] = 'application/pdf'
        response['Content-disposition'] = f'attachment; filename=macaron.pdf'
        return response
