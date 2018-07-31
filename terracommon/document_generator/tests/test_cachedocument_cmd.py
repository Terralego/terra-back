from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


@patch('terracommon.document_generator.management.'
       'commands.cache_document.CachedDocument',
       autospec=True)
class CacheDocumentCmdTestCase(TestCase):
    def setUp(self):
        self.filename = 'testfile.txt'

    def test_add_call(self, mock_cacheddoc):
        mock_cacheddoc_instance = mock_cacheddoc.return_value

        content = 'adadsadsad'
        call_command('cache_document', 'add', self.filename, f'-c{content}')

        mock_cacheddoc.assert_called_with(self.filename)
        mock_cacheddoc_instance.create_cache.assert_called_with(content, 'w')

    def test_add_call_with_binary_mode(self, mock_cacheddoc):
        mock_cacheddoc_instance = mock_cacheddoc.return_value

        content = 'some content'
        call_command('cache_document',
                     'add', self.filename,
                     f'-c{content}',
                     '-b')

        mock_cacheddoc.assert_called_with(self.filename)
        mock_cacheddoc_instance.create_cache.assert_called_with(content, 'wb')

    def test_delete_call(self, mock_cacheddoc):
        mock_cacheddoc_instance = mock_cacheddoc.return_value

        call_command('cache_document', 'delete', self.filename)

        mock_cacheddoc.assert_called_with(self.filename)
        mock_cacheddoc_instance.delete_cache.assert_called()
