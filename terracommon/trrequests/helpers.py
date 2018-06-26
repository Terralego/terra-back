import os
import uuid


class UploadFileHelpers:

    @staticmethod
    def rename_file(instance, filename):
        return os.path.join('uploads', f'{uuid.uuid4()}')
