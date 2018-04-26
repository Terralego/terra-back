import csv
import tempfile

from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import TestCase

from terra.models import Layer, Feature


class ImportCompaniesTestCase(TestCase):
    def call_command_with_tempfile(self, csv_rows, args=None, opts=None):
        if args is None:
            args = []
        if opts is None:
            opts = {}
        with tempfile.NamedTemporaryFile(mode='w', delete=True, dir='.', suffix='.csv') as tf:
            with open(tf.name, 'w') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerows(csv_rows)
            args += [f'--source={f.name}']
            call_command('import_companies', *args, **opts)

    def test_simple_import(self):
        company_layer = Layer.objects.get_or_create(name='company')[0]
        initial = company_layer.features.all().count()
        self.call_command_with_tempfile(
            csv_rows=[['SIREN', 'NIC', 'L1_NORMALISEE', 'L2_NORMALISEE', 'L3_NORMALISEE'],
                      ['822869632', '00023', '52 RUE JACQUES BABINET', '31100 TOULOUSE', 'France']]
        )
        expected = initial + 1
        self.assertEqual(company_layer.features.all().count(), expected)

    def test_init_options(self):
        company_layer = Layer.objects.get_or_create(name='company')[0]
        for i in range(2):
            Feature.objects.create(geom=Point(), properties={'SIREN': '', 'NIC': ''}, layer=company_layer)
        self.assertEqual(company_layer.features.all().count(), 2)
        self.call_command_with_tempfile(
            csv_rows=[['SIREN', 'NIC', 'L1_NORMALISEE', 'L2_NORMALISEE', 'L3_NORMALISEE'],
                      ['518521414', '00038', '11 RUE DU MARCHIX', '44000 NANTES', 'France'],
                      ['518521414', '00053', '52 RUE JACQUES BABINET', '31100 TOULOUSE', 'France'],
                      ['813792686', '00012', 'BOIS DE TULLE', '32700 LECTOURE', 'France'],
                      ['822869632', '00023', '52 RUE JACQUES BABINET', '31100 TOULOUSE', 'France']],
            args=[
                '--init',
                '--creations-per-transaction=3',
                '--bulk'
            ]
        )
        self.assertEqual(company_layer.features.all().count(), 4)
        feature = Feature.objects.get(layer=company_layer, properties__SIREN='813792686', properties__NIC='00012')
        self.assertEqual(feature.properties.get('L1_NORMALISEE', ''), 'BOIS DE TULLE')

    def test_import_with_creations_and_updates(self):
        company_layer = Layer.objects.get_or_create(name='company')[0]
        Feature.objects.create(
            geom=Point(),
            properties={
                'SIREN': '437582422',
                'NIC': '00097',
                'L1_NORMALISEE': '36 RUE JACQUES BABINET',
                'L2_NORMALISEE': '31100 TOULOUSE',
                'L3_NORMALISEE': 'France',
            },
            layer=company_layer
        )
        initial = company_layer.features.all().count()
        self.call_command_with_tempfile(
            csv_rows=[['SIREN', 'NIC', 'L1_NORMALISEE', 'L2_NORMALISEE', 'L3_NORMALISEE'],
                      ['437582422', '00097', '52 RUE JACQUES BABINET', '31100 TOULOUSE', 'France'],
                      ['518521414', '00038', '11 RUE DU MARCHIX', '44000 NANTES', 'France']]
        )
        expected = initial + 1
        self.assertEqual(company_layer.features.all().count(), expected)
        feature = Feature.objects.get(layer=company_layer, properties__SIREN='437582422', properties__NIC='00097')
        self.assertEqual(feature.properties.get('L1_NORMALISEE', ''), '52 RUE JACQUES BABINET')
