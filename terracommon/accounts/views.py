from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .forms import PasswordSetAndResetForm
from .serializers import PasswordResetSerializer, UserProfileSerializer


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return get_user_model().objects.none()


class UserRegisterView(GenericAPIView):
    permission_classes = (AllowAny, )

    def post(self, request):
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


class UserSetPasswordView(GenericAPIView):
    permission_classes = (AllowAny, )

    def post(self, request, uidb64, token):
        serializer = PasswordResetSerializer(uidb64, token, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({'detail': 'Password has been changed'})
