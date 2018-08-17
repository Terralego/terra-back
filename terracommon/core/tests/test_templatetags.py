from django.template import Context, Template
from django.test import TestCase


class TemplatesTagsTestCase(TestCase):

    def test_front_url(self):
        front_url = 'http://myfront/'
        with self.settings(FRONT_URL=front_url):
            context = Context()
            template_to_render = Template(
                '{% load settings_tags %}'
                '{% front_url %}'
            )

            rendered = template_to_render.render(context)

            self.assertEqual(rendered, front_url)
