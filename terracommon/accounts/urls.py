from django.conf.urls import url

from .views import UserProfileView, UserRegisterView, UserSetPasswordView

app_name = 'terracommon.accounts'

urlpatterns = [
    url(r'^accounts/user/$', UserProfileView.as_view(), name='profile'),
    url(r'^accounts/register/$', UserRegisterView.as_view(), name='register'),
    url((r'^accounts/change-password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        UserSetPasswordView.as_view(), name='reset-password'),
]
