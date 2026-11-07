"""Шаг 2: изоляция контактов клиники и сохранение доступа."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class VetShellTests(TestCase):
    def test_shell_does_not_adopt_seeded_contacts(self):
        from .models import ContactSettings
        ContactSettings.objects.update_or_create(pk=1, defaults={
            'phone_primary': '+7 (988) 580-88-99', 'address': 'Другой проект',
            'map_url': 'https://example.com/map', 'is_published': True,
        })
        for url in ['/', '/catalog/', reverse('users:login')]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                header = html.split('<header class="va-header"', 1)[1].split('</header>', 1)[0]
                self.assertNotIn('tel:', header)
                self.assertNotIn('Другой проект', header)
                self.assertEqual(html.count('data-vet-header'), 1)
                self.assertEqual(html.count('search/js/search.js'), 1)

    @override_settings(VET_CLINIC_PHONE='+7 (900) 123-45-67')
    def test_explicit_clinic_phone(self):
        self.assertContains(self.client.get(reverse('users:login')), 'href="tel:+79001234567"')

    def test_logout_stays_post_with_csrf(self):
        user = get_user_model().objects.create_user(username='vet-shell-user')
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        response = client.get('/')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'action="' + reverse('users:logout') + '" method="post"')
        self.assertEqual(client.get(reverse('users:logout')).status_code, 405)
        self.assertEqual(client.post(reverse('users:logout')).status_code, 403)

    @override_settings(VET_CLINIC_USE_ADMIN_CONTACTS=True, VET_CLINIC_PHONE='+7 (900) 999-00-00')
    def test_shell_uses_published_admin_phone(self):
        from .models import ContactSettings

        record, _ = ContactSettings.objects.update_or_create(pk=1, defaults={
            'phone_primary': '+7 (900) 111-22-33', 'is_published': True,
        })
        for url in ('/', reverse('users:login')):
            response = self.client.get(url)
            self.assertContains(response, 'class="va-phone" href="tel:+79001112233"', count=2)
            self.assertNotContains(response, 'tel:+79009990000')

        record.is_published = False
        record.save(update_fields=['is_published'])
        response = self.client.get(reverse('users:login'))
        self.assertNotContains(response, 'tel:+79001112233')
        self.assertNotContains(response, 'tel:+79009990000')
