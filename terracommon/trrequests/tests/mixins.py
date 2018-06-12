from django.contrib.auth.models import Permission


class TestPermissionsMixin:

    def _clean_permissions(self):
        self.user.user_permissions.clear()
        self._clean_perm_cache()

    def _set_permissions(self, perms):
        for perm in perms:
            permission = Permission.objects.get(codename=perm)
            self.user.user_permissions.add(permission)
        self._clean_perm_cache()

    def _clean_perm_cache(self):
        for cache in ['_user_perm_cache', '_perm_cache']:
            if hasattr(self.user, cache):
                delattr(self.user, cache)
