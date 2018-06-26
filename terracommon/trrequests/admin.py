from django.contrib import admin

from .models import Comment, UploadFile, UserRequest


class UploadFileAdmin(admin.TabularInline):
    model = UploadFile


class CommentAdmin(admin.ModelAdmin):
    inlines = (UploadFileAdmin, )


admin.site.register(UserRequest)
admin.site.register(Comment, CommentAdmin)
