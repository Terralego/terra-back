from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import detail_route
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from url_filter.integrations.drf import DjangoFilterBackend

from terracommon.core.filters import JSONFieldOrderingFilter
from terracommon.events.signals import event

from .forms import PasswordSetAndResetForm
from .serializers import (PasswordChangeSerializer, PasswordResetSerializer,
                          TerraUserSerializer, UserProfileSerializer)

UserModel = get_user_model()


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
            form = PasswordSetAndResetForm(data=request.data)
            if form.is_valid():
                user = get_user_model().objects.create(
                    **{
                        get_user_model().EMAIL_FIELD: request.data['email'],
                        'is_active': True,
                    })
                user.set_unusable_password()
                user.save()

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
            return Response({}, status=status.HTTP_200_OK)


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
            'jwt_delta': settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
        }

        terra_settings.update(settings.TERRA_APPLIANCE_SETTINGS)

        return Response(terra_settings)


class UserInformationsView(APIView):
    def get(self, request):
        user = self.request.user
        return Response(TerraUserSerializer(user).data)


class UserViewSet(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    parser_classes = (JSONParser, )
    serializer_class = TerraUserSerializer
    queryset = UserModel.objects.none()
    filter_backends = (DjangoFilterBackend, JSONFieldOrderingFilter,
                       SearchFilter, )
    search_fields = ('uuid', 'email', 'properties', )
    filter_fields = ('uuid', 'email', 'properties', 'groups')

    def get_queryset(self):
        if self.request.user.has_perm('accounts.can_manage_users'):
            return UserModel.objects.all()

        return self.queryset

    @detail_route(methods=['post', ])
    def groups(self, request, pk=None):
        user = get_object_or_404(UserModel, pk=pk)

        defined_groups = []

        for group in request.data['groups']:
            defined_groups.append(get_object_or_404(Group, name=group))

        user.groups.set(defined_groups)

        return Response(
            [g.name for g in defined_groups],
            status=status.HTTP_200_OK)
