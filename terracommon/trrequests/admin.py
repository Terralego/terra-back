from django.contrib import admin

from .models import Comment, UserRequest

admin.site.register(UserRequest)
admin.site.register(Comment)
