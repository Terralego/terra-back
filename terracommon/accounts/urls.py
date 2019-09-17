from django.conf.urls import url
from django.urls import path
from rest_framework import routers

from .views import (GroupViewSet, SettingsView, UserChangePasswordView,
                    UserInformationsView, UserProfileView, UserRegisterView,
                    UserSetPasswordView, UserViewSet)

app_name = 'accounts'

router = routers.SimpleRouter()
router.register(r'user', UserViewSet, base_name='user')
router.register(r'groups', GroupViewSet, base_name='group')
urlpatterns = router.urls

urlpatterns += [
    path(r'settings/', SettingsView.as_view(), name='settings'),
    url(r'^auth/user/', UserInformationsView.as_view()),
    url(r'^accounts/user/$', UserProfileView.as_view(), name='profile'),
    url(r'^accounts/register/$', UserRegisterView.as_view(), name='register'),
    url((r'^accounts/change-password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        UserSetPasswordView.as_view(), name='reset-password'),
    url(r'^accounts/change-password/reset/',
        UserChangePasswordView.as_view(), name='new-password'),
]
