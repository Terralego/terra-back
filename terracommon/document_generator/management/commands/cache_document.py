from django.core.management import BaseCommand, CommandParser

from terracommon.document_generator.helpers import CachedDocument


class Command(BaseCommand):
    def add_arguments(self, parser):
        cmd = self

        class SubParser(CommandParser):
            def __init__(self, *args, **kwargs):
                super(SubParser, self).__init__(cmd, **kwargs)

        subparser = parser.add_subparsers(help='command to add or '
                                               'delete a cache file',
                                          dest='command',
                                          parser_class=SubParser)

        parser_add = subparser.add_parser('add',
                                          help='create a cache file '
                                               'and add content to it')
        parser_add.add_argument('file',
                                help='name of the file to create')
        parser_add.add_argument('-c',
                                '--content',
                                help='content to write in the cache file',
                                required=True)
        parser_add.add_argument('-b',
                                '--binary',
                                action='store_true',
                                help='specify if the file is binary')

        parser_delete = subparser.add_parser('delete',
                                             help='delete a cache file')
        parser_delete.add_argument('file',
                                   help='name of the cache file to delete')

    def handle(self, *args, **options):
        document = CachedDocument(options['file'])

        if options['command'] == 'delete':
            document.delete_cache()
        elif options['command'] == 'add':
            writing_mode = 'wb' if options['binary'] else 'w'
            document.create_cache(options['content'], writing_mode)
