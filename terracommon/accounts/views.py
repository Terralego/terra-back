from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from terracommon.events.signals import event

from .forms import PasswordSetAndResetForm
from .serializers import (PasswordChangeSerializer, PasswordResetSerializer,
                          TerraUserSerializer, UserProfileSerializer)


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return get_user_model().objects.none()


class UserRegisterView(APIView):
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

                serializer = TerraUserSerializer(user)
                event.send(
                    self.__class__,
                    action="USER_CREATED",
                    user=user,
                    instance=user
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(data=form.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(status=status.HTTP_200_OK)


class UserSetPasswordView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, uidb64, token):
        serializer = PasswordResetSerializer(uidb64, token, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({'detail': 'Password has been changed'})


class UserChangePasswordView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        serializer = PasswordChangeSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({'detail': 'Password has been changed'})


class SettingsView(APIView):
    permission_classes = ()

    def get(self, request):
        terra_settings = {
            'states': {
                y: x
                for x, y in settings.STATES.VALUE_TO_CONST.items()
                },
        }

        terra_settings.update(settings.TERRA_APPLIANCE_SETTINGS)

        return Response(terra_settings)


class UserInformationsView(APIView):
    def get(self, request):
        user = self.request.user
        return Response(TerraUserSerializer(user).data)
