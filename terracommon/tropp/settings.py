from ..core.settings import *

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

INSTALLED_APPS += (
    'versatileimagefield',
)

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'tropp': [
        ('full_size', 'url'),
        ('thumbnail', 'thumbnail__250x190'),
    ]
}

TROPP_BASE_LAYER_NAME = 'Base opp layer'
