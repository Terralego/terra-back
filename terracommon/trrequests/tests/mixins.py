from django.contrib.auth.models import Permission


class TestPermissionsMixin:

    def _clean_permissions(self):
        self.user.user_permissions.clear()
        self._clean_perm_cache()

    def _set_permissions(self, perms):
        self.user.user_permissions.add(
            *Permission.objects.filter(codename__in=perms)
        )
        self._clean_perm_cache()

    def _clean_perm_cache(self):
        for cache in ['_user_perm_cache', '_perm_cache']:
            if hasattr(self.user, cache):
                delattr(self.user, cache)
