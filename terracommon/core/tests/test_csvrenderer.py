from django.test import TestCase

from terracommon.core.renderers import CSVRenderer


class CSVRendererTestCase(TestCase):
    def setUp(self):
        self.data = {
            'letters': {
                'vowels': ['a', 'e', 'i', 'o', 'u'],
                'last_letter': 'z'
            },
            'number': '42',
        }

    def test_render_method(self):
        csv_renderer = CSVRenderer()
        csv_content = csv_renderer.render(self.data)
        self.assertTrue(isinstance(csv_content, str))
