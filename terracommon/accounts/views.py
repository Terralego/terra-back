from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.utils import IntegrityError
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from .forms import PasswordSetAndResetForm


class UserViewSet(viewsets.ModelViewSet):

    @list_route(methods=['post', 'get'], permission_classes=[])
    def register(self, request):
        try:
            user = get_user_model().objects.create(
                **{
                    get_user_model().EMAIL_FIELD: request.data['email'],
                    'is_active': True,
                })
            user.set_unusable_password()
            user.save()

            form = PasswordSetAndResetForm(data=request.data)
            if form.is_valid():
                opts = {
                    'token_generator': default_token_generator,
                    'from_email': settings.DEFAULT_FROM_EMAIL,
                    'email_template_name':
                        'registration/registration_email.txt',
                    'subject_template_name':
                        'registration/registration_email_subject.txt',
                    'request': self.request,
                    'html_email_template_name':
                        'registration/registration_email.html',
                }
                form.save(**opts)
                return Response(status=200)
            else:
                return Response(data=form.errors, status=400)
        except IntegrityError:
            return Response(status=409)
