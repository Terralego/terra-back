DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'tropp': [
        ('full_size', 'url'),
        ('thumbnail', 'thumbnail__250x190'),
    ]
}
