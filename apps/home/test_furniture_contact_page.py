from django.test import TestCase, override_settings
from django.urls import reverse

from apps.home.models import ContactSettings


@override_settings(VET_CLINIC_PHONE='', VET_CLINIC_ADDRESS='',
                   VET_CLINIC_HOURS='', VET_CLINIC_MAP_URL='')
class VetContactPageTests(TestCase):
    def setUp(self):
        self.url = reverse('furniture_contacts')

    def test_missing_clinic_contacts_do_not_expose_workshop_record(self):
        ContactSettings.objects.update_or_create(pk=1, defaults={
            'is_published': True, 'address': 'Адрес мастерской',
            'phone_primary': '+7 (900) 123-45-67',
        })
        response = self.client.get(self.url)
        self.assertContains(response, 'Контакты пока не опубликованы')
        self.assertContains(response, f'href="{reverse("home")}#callback"')
        self.assertNotContains(response, 'Адрес мастерской')
        self.assertNotContains(response, 'tel:+79001234567')

    @override_settings(VET_CLINIC_PHONE='+7 (900) 111-22-33',
                       VET_CLINIC_ADDRESS='Тестовый адрес',
                       VET_CLINIC_HOURS='10:00–18:00',
                       VET_CLINIC_MAP_URL='https://maps.example.test/clinic')
    def test_configured_contacts(self):
        response = self.client.get(self.url)
        for value in ('tel:+79001112233', 'Тестовый адрес', '10:00–18:00',
                      'https://maps.example.test/clinic'):
            self.assertContains(response, value)

    @override_settings(VET_CLINIC_MAP_URL='javascript:bad()',
                       VET_CLINIC_ADDRESS='<script>bad()</script>')
    def test_contact_values_are_safe(self):
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, 'javascript:bad()')

    def test_navigation_and_sitemap(self):
        self.assertContains(self.client.get('/'), f'href="{self.url}"')
        self.assertContains(self.client.get('/sitemap-pages.xml'), self.url)
