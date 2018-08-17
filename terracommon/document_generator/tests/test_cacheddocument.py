import os
from tempfile import NamedTemporaryFile, TemporaryFile

from django.conf import settings
from django.test import TestCase

from terracommon.document_generator.helpers import CachedDocument


class CachedDocumentTestCase(TestCase):
    def test_CachedDocument_create_delete(self):
        with open('testcreate.txt', 'w') as f:
            cache_file = CachedDocument(f)
        self.assertTrue(os.path.isfile(cache_file.name))

        cache_file.remove()
        self.assertFalse(os.path.isfile(cache_file.name))

    def test_CachedDocument_from_existing_file(self):
        tmp_file = NamedTemporaryFile(mode='w',
                                      dir=settings.MEDIA_ROOT,
                                      delete=False)
        tmp_file.close()

        cache_file = CachedDocument(tmp_file)
        self.assertEqual(tmp_file.name, cache_file.name)
        self.assertTrue(os.path.isfile(cache_file.name))

        cache_file.remove()
        self.assertFalse(os.path.isfile(cache_file.name))
        self.assertFalse(os.path.isfile(tmp_file.name))

    def test_CachedDocument_create_from_other_file(self):
        with TemporaryFile() as tmp_file:
            tmp_file.write(b'content file')
            tmp_file.seek(0)
            content = tmp_file.read()

        with open('test.text', 'wb') as f:
            f.write(content)
            cache_file = CachedDocument(f)

        self.assertTrue(os.path.isfile(cache_file.name))

        cache_file.remove()
        self.assertFalse(os.path.isfile(cache_file.name))
