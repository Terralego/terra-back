import csv
import tempfile

from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import TestCase

from terra.models import Layer, Feature


class ImportCompaniesTestCase(TestCase):
    def call_command_with_tempfile(self, csv_rows, args=[], opts={}):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='.', suffix='.csv') as tf:
            with open(tf.name, 'w') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerows(csv_rows)
            args += [f'--source={f.name}']
            call_command('import_insee', *args, **opts)

    def test_simple_import(self):
        insee_layer = Layer.objects.get_or_create(name='insee')[0]
        initial = insee_layer.features.all().count()
        self.call_command_with_tempfile(
            csv_rows=[
                ['CODGEO', 'Nb Pharmacies et parfumerie', 'Dynamique Entrepreneuriale', 'Nb Résidences Principales',
                 'Nb propriétaire', 'Nb Logement', 'Nb Résidences Secondaires', 'Nb Log Vacants',
                 'Nb Occupants Résidence Principale', 'Nb Femme', 'Nb Homme', 'Nb Mineurs', 'Nb Majeurs',
                 'Nb Etudiants', 'CP'],
                [1006, 0, 42, 41, 28, 57, 13, 3, 86, 86, 86, 101, 71, 2, 1]]
        )
        expected = initial + 1
        self.assertEqual(insee_layer.features.all().count(), expected)

    def test_init_options(self):
        insee_layer = Layer.objects.get_or_create(name='insee')[0]
        for i in range(2):
            Feature.objects.create(geom=Point(), properties={'SIREN': '', 'NIC': ''}, layer=insee_layer)
        self.assertEqual(insee_layer.features.all().count(), 2)
        self.call_command_with_tempfile(
            csv_rows=[
                ['CODGEO', 'Nb Pharmacies et parfumerie', 'Dynamique Entrepreneuriale', 'Nb Résidences Principales',
                 'Nb propriétaire', 'Nb Logement', 'Nb Résidences Secondaires', 'Nb Log Vacants',
                 'Nb Occupants Résidence Principale', 'Nb Femme', 'Nb Homme', 'Nb Mineurs', 'Nb Majeurs',
                 'Nb Etudiants', 'CP'],
                [1002, 0, 45, 67, 61, 142, 71, 4, 168, 162, 164, 202, 124, 5, 1],
                [1004, 0, 634, 4635, 1968, 5184, 135, 414, 11015, 11350, 10878, 13624, 8604, 904, 1],
                [1005, 0, 113, 473, 344, 505, 14, 18, 1406, 1324, 1402, 1758, 968, 97, 1],
                [1006, 0, 42, 41, 28, 57, 13, 3, 86, 86, 86, 101, 71, 2, 1]],
            args=[
                '--init',
                '--creations-per-transaction=3',
                '--bulk'
            ]
        )
        self.assertEqual(insee_layer.features.all().count(), 4)
        feature = Feature.objects.get(layer=insee_layer, properties__CODGEO='1005')
        self.assertEqual(feature.properties.get('Dynamique Entrepreneuriale'), '113')

    def test_import_with_creations_and_updates(self):
        insee_layer = Layer.objects.get_or_create(name='insee')[0]
        Feature.objects.create(
            geom=Point(),
            properties={
                'CODGEO': '1001',
                'Dynamique Entrepreneuriale': '42'
            },
            layer=insee_layer
        )
        initial = insee_layer.features.all().count()
        self.call_command_with_tempfile(
            csv_rows=[
                ['CODGEO', 'Nb Pharmacies et parfumerie', 'Dynamique Entrepreneuriale', 'Nb Résidences Principales',
                 'Nb propriétaire', 'Nb Logement', 'Nb Résidences Secondaires', 'Nb Log Vacants',
                 'Nb Occupants Résidence Principale', 'Nb Femme', 'Nb Homme', 'Nb Mineurs', 'Nb Majeurs',
                 'Nb Etudiants', 'CP'],
                [1001, 0, 57, 248, 196, 289, 32, 9, 728, 694, 714, 909, 499, 51, 1],
                [1002, 0, 45, 67, 61, 142, 71, 4, 168, 162, 164, 202, 124, 5, 1]]
        )
        expected = initial + 1
        self.assertEqual(insee_layer.features.all().count(), expected)
        feature = Feature.objects.get(layer=insee_layer, properties__CODGEO='1001')
        self.assertEqual(feature.properties.get('Dynamique Entrepreneuriale'), '57')
