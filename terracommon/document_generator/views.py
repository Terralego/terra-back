from django.http.response import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import detail_route

from terracommon.trrequests.models import UserRequest

from .helpers import DocumentGenerator
from .models import OdtFile


class OdtViewSets(viewsets.ViewSet):
    @detail_route(methods=['POST'],
                  url_name='pdf-creator',
                  url_path='pdf_creator/(?P<userreq_id>[^/.]+)')
    def pdf_creator(self, request, pk=None, userreq_id=None):
        userrequest = UserRequest.objects.get(pk=userreq_id)

        myodt = OdtFile.objects.get(pk=pk)
        myodt_path = str(myodt.odt)

        pdf_generator = DocumentGenerator(myodt_path)
        pdf = pdf_generator.get_pdf(userrequest.properties)

        response = HttpResponse(pdf)
        response['Content-Type'] = 'application/pdf'
        response['Content-disposition'] = f'attachment; filename=macaron.pdf'
        return response
