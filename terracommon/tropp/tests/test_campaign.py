from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.core.settings import STATES
from terracommon.tropp.tests.factories import CampaignFactory, ViewpointFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class CampaignTestCase(TestPermissionsMixin, APITestCase):
    def setUp(self):
        self.photograph = TerraUserFactory()
        self.user = TerraUserFactory()
        self._set_permissions([
            'manage_all_campaigns',
            'add_campaign',
        ])

    def test_list_campaign(self):
        viewpoint2 = ViewpointFactory()
        viewpoint = ViewpointFactory()
        campaign = CampaignFactory(assignee=self.photograph)
        campaign.viewpoints.set([viewpoint, viewpoint2])

        campaign_other = CampaignFactory()  # campaign for other photograph

        list_url = reverse('tropp:campaign-list')
        campaign_url = resolve_url('tropp:campaign-detail', pk=campaign.pk)
        campaign_other_url = resolve_url('tropp:campaign-detail',
                                         pk=campaign_other.pk)

        # First we try as anonymous
        self.assertEqual(status.HTTP_401_UNAUTHORIZED,
                         self.client.get(list_url).status_code)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED,
                         self.client.get(campaign_url).status_code)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED,
                         self.client.get(campaign_other_url).status_code)

        # Then with no rights
        self.client.force_authenticate(user=self.photograph)
        response = self.client.get(list_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, response.data.get('count'))
        self.assertEqual(
            viewpoint.pictures.first().file.url.split('/'),
            response.data.get('results')[0].get('picture').get('original').split('/')
        )

        response = self.client.get(campaign_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            viewpoint.pictures.first().file.url,
            response.data.get('viewpoints')[0].get('picture').get('original')
        )
        self.assertEqual(status.HTTP_403_FORBIDDEN,
                         self.client.get(campaign_other_url).status_code)

        # Then as admin
        self.client.force_authenticate(user=self.user)
        response = self.client.get(list_url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, response.data.get('count'))

        self.assertEqual(status.HTTP_200_OK,
                         self.client.get(campaign_url).status_code)
        self.assertEqual(status.HTTP_200_OK,
                         self.client.get(campaign_other_url).status_code)

    @override_settings(TROPP_PICTURES_STATES_WORKFLOW=True)
    def test_get_campaign(self):
        campaign = CampaignFactory(assignee=self.photograph)
        campaign_url = resolve_url('tropp:campaign-detail', pk=campaign.pk)
        list_url = resolve_url('tropp:campaign-list')
        self.client.force_authenticate(user=self.photograph)

        viewpoint = ViewpointFactory()
        viewpoint.pictures.all().delete()
        campaign.viewpoints.set([viewpoint])
        response = self.client.get(campaign_url)
        self.assertEqual(
            'Missing',
            response.data.get('viewpoints')[0].get('status')
        )
        response = self.client.get(list_url)
        self.assertEqual(
            1,
            response.data.get('results')[0].get('statistics').get('missing')
        )

        viewpoint = ViewpointFactory()
        campaign.viewpoints.set([viewpoint])
        response = self.client.get(campaign_url)
        self.assertEqual(
            'Draft',
            response.data.get('viewpoints')[0].get('status')
        )
        response = self.client.get(list_url)
        self.assertEqual(
            1,
            response.data.get('results')[0].get('statistics').get('pending')
        )

    @override_settings(TROPP_PICTURES_STATES_WORKFLOW=True)
    def test_search_campaign(self):
        campaign = CampaignFactory(assignee=self.photograph)
        list_url = resolve_url('tropp:campaign-list')
        self.client.force_authenticate(user=self.user)

        viewpoint = ViewpointFactory()
        campaign.viewpoints.set([viewpoint])
        # Picture state is draft
        response = self.client.get(list_url, {'status': 0})
        self.assertEqual(1, response.data.get('count'))
        response = self.client.get(list_url, {'status': 1})
        self.assertEqual(0, response.data.get('count'))
        response = self.client.get(list_url, {'picture_status': 100})
        self.assertEqual(1, response.data.get('count'))
        response = self.client.get(list_url, {'picture_status': 200})
        self.assertEqual(0, response.data.get('count'))

        viewpoint.pictures.update(state=STATES.ACCEPTED)
        response = self.client.get(list_url, {'status': 0})
        self.assertEqual(0, response.data.get('count'))
        response = self.client.get(list_url, {'status': 1})
        self.assertEqual(1, response.data.get('count'))
        response = self.client.get(list_url, {'picture_status': 200})
        self.assertEqual(0, response.data.get('count'))
        response = self.client.get(list_url, {'picture_status': 300})
        self.assertEqual(1, response.data.get('count'))

    def test_post_campaign(self):
        data = {
            'label': "My campaign",
            'assignee': self.photograph.pk,
            'viewpoints': [ViewpointFactory().pk, ViewpointFactory().pk],
        }

        self.client.force_authenticate(user=self.photograph)
        response = self.client.post(reverse('tropp:campaign-list'), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('tropp:campaign-list'), data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
