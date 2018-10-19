

INSTALLED_APPS += (  # noqa
    'storages',
    'versatileimagefield',
)

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
