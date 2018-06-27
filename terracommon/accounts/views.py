from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from .forms import PasswordSetAndResetForm
from .serializers import PasswordResetSerializer


class UserViewSet(viewsets.ModelViewSet):

    @list_route(methods=['post', ], permission_classes=[])
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
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(data=form.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)

    @list_route(methods=['post', ],
                permission_classes=[],
                url_path=(r'reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
                          r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})'),
                url_name='reset-password')
    def reset_password(self, request, uidb64, token):
        serializer = PasswordResetSerializer(uidb64, token, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({'detail': 'Password has been changed'})
