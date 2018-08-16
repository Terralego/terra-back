from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from terracommon.document_generator.helpers import CachedDocument


class CachedDocumentTestCase(TestCase):
    def setUp(self):
        self.fake_dirname = f'{settings.MEDIA_ROOT}fake/dir/to/test'

    @patch('terracommon.document_generator.helpers.open')
    @patch('terracommon.document_generator.helpers.os.path')
    @patch('terracommon.document_generator.helpers.os')
    def test_create_cachefile(self, mock_os, mock_path, mock_open):
        # Force to pass in dir creation if dir don't exists
        mock_path.isdir.return_value = False
        mock_path.dirname.return_value = self.fake_dirname
        mock_path.abspath.return_value = self.fake_dirname

        # Accessing context manager open
        mock_open_ctx_manager = mock_open.return_value.__enter__.return_value

        testcache = CachedDocument('test.txt')
        testcache.create_cache('new content', 'w')

        mock_path.dirname.assert_called_with(testcache.path)
        mock_path.isdir.assert_called_with(self.fake_dirname)
        mock_os.makedirs.assert_called_with(self.fake_dirname)
        mock_open.assert_called_with(testcache.path, 'w')
        mock_open_ctx_manager.write.assert_called_with('new content')

    @patch('terracommon.document_generator.helpers.open')
    @patch('terracommon.document_generator.helpers.os.path')
    @patch('terracommon.document_generator.helpers.os')
    def test_create_cachefile_with_dir_exists(self,
                                              mock_os,
                                              mock_path,
                                              mock_open):
        # Force "dir exists" to check if makedirs is not called
        mock_path.isdir.return_value = True
        mock_path.dirname.return_value = self.fake_dirname
        mock_path.abspath.return_value = self.fake_dirname

        # Accessing context manager open
        mock_open_ctx_manager = mock_open.return_value.__enter__.return_value

        testcache = CachedDocument('test.txt')
        testcache.create_cache('new content', 'w')

        mock_path.dirname.assert_called_with(testcache.path)
        mock_path.isdir.assert_called_with(self.fake_dirname)
        mock_os.makedirs.assert_not_called()
        mock_open.assert_called_with(testcache.path, 'w')
        mock_open_ctx_manager.write.assert_called_with('new content')

    @patch('terracommon.document_generator.helpers.os')
    def test_delete_cachefile(self, mock_os):
        mock_os.path.abspath.return_value = self.fake_dirname

        fake_cachename = 'fake_cache.txt'
        fake_cache = CachedDocument(fake_cachename)
        fake_cache.delete_cache()

        mock_os.remove.assert_called_with(fake_cache.path)

    def test_unvalid_cachefile_path(self):
        with self.assertRaises(ValueError):
            CachedDocument('../../../etc/password')
