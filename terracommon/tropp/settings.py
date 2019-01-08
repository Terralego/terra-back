from ..core.settings import *

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

INSTALLED_APPS += (
    'versatileimagefield',
)

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'tropp': [
        ('original', 'url'),
        ('full', 'thumbnail__1500x1125'),
        ('list', 'thumbnail__300x225'),
        ('thumbnail', 'thumbnail__120x90'),
    ]
}

TROPP_BASE_LAYER_NAME = 'Base opp layer'

TROPP_PICTURES_STATES_WORKFLOW = True
