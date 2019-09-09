from django.conf.urls import url
from django.urls import path
from rest_framework import routers
from rest_framework_jwt import views as auth_views

from .views import (GroupViewSet, SettingsView, UserChangePasswordView,
                    UserInformationsView, UserProfileView, UserRegisterView,
                    UserSetPasswordView, UserViewSet)

app_name = 'accounts'

router = routers.SimpleRouter()
router.register(r'user', UserViewSet, base_name='user')
router.register(r'groups', GroupViewSet, base_name='group')
urlpatterns = router.urls

urlpatterns += [
    path('settings/', SettingsView.as_view(), name='settings'),
    path('auth/obtain-token/', auth_views.obtain_jwt_token, name='token-obtain'),
    path('auth/verify-token/', auth_views.verify_jwt_token, name='token-verify'),
    path('auth/refresh-token/', auth_views.refresh_jwt_token, name='token-refresh'),
    path('auth/user/', UserInformationsView.as_view()),
    path('accounts/user/', UserProfileView.as_view(), name='profile'),
    path('accounts/register/', UserRegisterView.as_view(), name='register'),
    url((r'^accounts/change-password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        UserSetPasswordView.as_view(), name='reset-password'),
    path('accounts/change-password/reset/', UserChangePasswordView.as_view(), name='new-password'),
]
