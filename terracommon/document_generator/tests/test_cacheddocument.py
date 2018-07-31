import os
from unittest.mock import patch

from django.test import TestCase

from terracommon.document_generator.helpers import CachedDocument


class CachedDocumentTestCase(TestCase):
    @patch('terracommon.document_generator.helpers.open')
    @patch('terracommon.document_generator.helpers.os')
    def test_create_cachefile(self, mock_makedir, mock_open):
        testcache = CachedDocument('test.txt')
        testdir = os.path.dirname(testcache.path)

        testcache.create_cache('new content', 'w')

        if not os.path.isdir(testdir):
            mock_makedir.makedir.assert_called_with(testdir)

        mock_open.assert_called_with(testcache.path, 'w')

    @patch('terracommon.document_generator.helpers.os')
    def test_delete_cachefile(self, mock_remove):
        fake_cachename = 'fake_cache.txt'
        fake_cache = CachedDocument(fake_cachename)
        fake_cache.delete_cache()

        mock_remove.remove.assert_called_with(fake_cache.path)
