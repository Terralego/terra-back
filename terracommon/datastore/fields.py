import base64
import binascii
import logging

from django.core.files import File
from rest_framework import serializers

logger = logging.getLogger(__name__)


class FileBase64Field(serializers.Field):
    def to_representation(self, value):
        if not isinstance(value, File):
            raise TypeError(
                f'Expect a django File object, instead get {type(value)}'
            )

        with value.open(mode='rb') as f:
            return base64.b64encode(f.read())

    def to_internal_value(self, data):
        try:
            encoded = data.split(",", 1)[1]

        # Caught the error to log it then re-raised it
        except IndexError:
            logger.warning(
                f"cannot read document {data}"
            )
            raise serializers.ValidationError(
                'document field must be "data/<format>;base64,<code>" format'
            )

        else:
            try:

                decoded = base64.b64decode(encoded)
            # Caught the error to log it then re-raised it
            except binascii.Error:
                logger.warning(f'{data} is not a base64 format')
                raise serializers.ValidationError(
                    f'expected a base64, get instead {type(data)}'
                )

        return decoded
