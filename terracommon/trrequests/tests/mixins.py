from django.contrib.auth.models import Permission


class TestPermissionsMixin:

    def _clean_permissions(self):
        self.user.user_permissions.all().delete()

    def _set_permissions(self, perms):
        for perm in perms:
            permission = Permission.objects.get(codename=perm)
            self.user.user_permissions.add(permission)
        delattr(self.user, '_user_perm_cache')
        delattr(self.user, '_perm_cache')
