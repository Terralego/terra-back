import os


def rename_comment_attachment(instance, filename):
    return os.path.join('uploads', f'comment-{instance.pk}')
