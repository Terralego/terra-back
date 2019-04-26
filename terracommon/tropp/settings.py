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
        ('thumbnail', 'thumbnail__180x120'),
    ]
}

TROPP_BASE_LAYER_NAME = 'Base opp layer'

TROPP_PICTURES_STATES_WORKFLOW = False

TROPP_VIEWPOINT_PROPERTIES_SET = {
    'pdf': {
        ('camera', 'Appareil photo'),
    },
    'form': {},
    'filter': {},
}

TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT = [
    'commune',
]

TROPP_SEARCHABLE_PROPERTIES = {
    'cities': {
        'json_key': 'commune',
        'type': 'single',
    },
    'themes': {
        'json_key': 'themes',
        'type': 'many',
    },
    'road': {
        'json_key': 'voie',
        'type': 'text',
    },
    'site': {
        'json_key': 'site',
        'type': 'text',
    },
}
