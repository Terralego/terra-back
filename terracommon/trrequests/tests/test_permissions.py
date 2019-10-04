from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.generics import ListCreateAPIView
from rest_framework.test import APIRequestFactory
from terra_accounts.tests.factories import TerraUserFactory

from terracommon.trrequests.permissions import IsOwnerOrStaff
from terracommon.trrequests.tests.factories import UserRequestFactory

factory = APIRequestFactory()
UserModel = get_user_model()


class TestView(ListCreateAPIView):
    """ view class only created for testing purpose """
    permission_classes = [IsOwnerOrStaff, ]


class IsOwnerOrSatffTestCase(TestCase):
    def setUp(self):
        self.permission = IsOwnerOrStaff()
        self.view = TestView.as_view()
        self.request = factory.get('/')  # we don't care about the path
        self.user = TerraUserFactory()
        self.request.user = self.user
        self.userrequest = UserRequestFactory()

    def test_has_object_permission_without_permissions(self):
        self.assertFalse(
            self.permission.has_object_permission(
                self.request,
                self.view,
                self.userrequest  # Need an object with owner field
            )
        )

    def test_has_object_permission_with_permissions(self):
        user_request = UserRequestFactory()
        user_request.owner = self.user
        self.assertTrue(
            self.permission.has_object_permission(
                self.request,
                self.view,
                user_request,
            )
        )

    def test_has_object_permission_with_staff(self):
        user = TerraUserFactory()
        user.is_staff = True
        request = factory.get('/')
        request.user = user
        self.assertTrue(
            self.permission.has_object_permission(
                request,
                self.view,
                self.userrequest,
            )
        )

    def test_has_object_permission_with_superuser(self):
        user = UserModel.objects.create_superuser(
            'admin@admin.com',
            'password',
        )
        request = factory.get('/')
        request.user = user
        self.assertTrue(
            self.permission.has_object_permission(
                request,
                self.view,
                self.userrequest,
            )
        )
