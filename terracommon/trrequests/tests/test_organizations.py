from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.trrequests.models import Organization
from terracommon.terra.tests.factories import TerraUserFactory


class OrganizationTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = TerraUserFactory(organizations=1)
        self.client.force_authenticate(user=self.user)

    def test_organization_creation(self):
        response = self.client.post(
            reverse('organization-list'),
            {
                'properties': {
                    'myproperty': 'myvalue',
                },

            }, format='json')

        self.assertEqual(201, response.status_code)

        response = response.json()
        organization = Organization.objects.get(pk=response.get('id'))
        self.assertEqual(list(organization.owner.all()), [self.user, ])
        self.assertEqual(organization.properties.get('myproperty'), 'myvalue')

        response = self.client.get(reverse('organization-list'))
        self.assertEqual(200, response.status_code)
        response = response.json()

        """This owner have two organizations, one created in user creation 
           process, and one during this test.
        """
        self.assertEqual(2, len(response))
        