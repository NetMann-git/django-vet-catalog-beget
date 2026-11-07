"""Шаг 6: прежний URL услуг теперь показывает только услуги клиники."""
from decimal import Decimal
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse, resolve
from .models import ClinicService, TeamMember


class ClinicServicesTests(TestCase):
    def setUp(self):
        self.url = reverse('furniture_services')

    def service(self, **kwargs):
        values = dict(name='Первичный приём', slug='primary', group='Терапия', is_published=True)
        values.update(kwargs)
        return ClinicService.objects.create(**values)

    def test_empty_state_and_original_data_are_preserved(self):
        staff = TeamMember.objects.create(name='Сотрудник исходного проекта', position='Менеджер')
        response = self.client.get(self.url)
        self.assertContains(response, 'Информация об услугах скоро появится')
        self.assertNotContains(response, 'Мебель и столярные работы')
        self.assertNotContains(response, 'LUSTRID')
        self.assertNotContains(response, 'Сотрудник исходного проекта')
        self.assertTrue(TeamMember.objects.filter(pk=staff.pk).exists())
        self.assertEqual(ClinicService.objects.count(), 0)

    def test_drafts_are_absent_from_list_search_and_group_options(self):
        self.service(name='Секретная услуга', group='Скрытое направление', is_published=False)
        self.service(name='Опубликованная услуга', slug='visible')
        response = self.client.get(self.url)
        self.assertContains(response, 'Опубликованная услуга')
        self.assertNotContains(response, 'Секретная услуга')
        self.assertNotContains(response, 'Скрытое направление')
        response = self.client.get(self.url, {'q': 'Секретная'})
        self.assertContains(response, 'По вашему запросу ничего не найдено')
        self.assertNotContains(response, 'Секретная услуга')

    def test_cyrillic_search_group_and_safe_text(self):
        self.service(name='УЗИ питомца', group='Диагностика', summary='<script>alert(1)</script>')
        self.service(name='Другой приём', slug='other')
        response = self.client.get(self.url, {'q': 'узи', 'group': 'Диагностика'})
        self.assertContains(response, 'УЗИ питомца')
        self.assertNotContains(response, 'Другой приём')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_prices_zero_missing_and_from(self):
        self.service(price=Decimal('0'))
        self.service(name='Услуга с ценой от', slug='from', price=Decimal('1500'), price_from=True, price_note='Пояснение к цене')
        self.service(name='Услуга без цены', slug='unknown')
        response = self.client.get(self.url)
        self.assertContains(response, '0,00 ₽')
        self.assertContains(response, '<span>от </span>')
        self.assertContains(response, 'Стоимость уточняется')
        self.assertContains(response, 'Пояснение к цене')

    def test_pagination_preserves_filters(self):
        for index in range(14):
            self.service(name=f'Приём {index:02}', slug=f'visit-{index}')
        response = self.client.get(self.url, {'q': 'приём', 'group': 'Терапия'})
        self.assertEqual(len(response.context['page_obj']), 12)
        soup = BeautifulSoup(response.content, 'html.parser')
        href = soup.select_one('.vs-pagination a')['href']
        query = parse_qs(urlsplit(href).query)
        self.assertEqual(query, {'q': ['приём'], 'group': ['Терапия'], 'page': ['2']})
        self.assertEqual(len(self.client.get(self.url, query).context['page_obj']), 2)

    def test_price_validation_and_unique_slug(self):
        self.service()
        bad = ClinicService(name='Другая', slug='another', price=Decimal('-1'))
        with self.assertRaises(ValidationError):
            bad.full_clean()
        duplicate = ClinicService(name='Другая', slug='primary')
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_admin_permissions_and_default_draft(self):
        admin_url = reverse('admin:home_clinicservice_changelist')
        self.assertEqual(self.client.get(admin_url).status_code, 302)
        user = get_user_model().objects.create_user('staff-no-service-permission', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(admin_url).status_code, 403)
        user.is_superuser = True
        user.save()
        self.assertEqual(self.client.get(admin_url).status_code, 200)
        response = self.client.post(reverse('admin:home_clinicservice_add'), {
            'name': 'Услуга администратора', 'slug': 'admin-service', 'sort_order': '100',
            'group': '', 'summary': '', 'description': '', 'preparation': '', 'price': '', 'price_note': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ClinicService.objects.get(slug='admin-service').is_published)

    def test_route_navigation_sitemap_and_tooltips_remain(self):
        self.assertEqual(self.url, '/services/')
        self.assertEqual(resolve(self.url).url_name, 'furniture_services')
        self.assertContains(self.client.get('/'), 'href="' + self.url + '"')
        response = self.client.get(self.url)
        self.assertContains(response, 'site-action-help.js')
        self.assertContains(response, 'data-help=')
        self.assertContains(response, reverse('home') + '#callback')
        self.assertContains(self.client.get('/sitemap-pages.xml'), self.url)

    def test_detail_supports_cyrillic_and_hides_drafts(self):
        service = self.service(slug='приём', description='<script>alert(1)</script>',
                               preparation='Возьмите документы питомца')
        url = reverse('clinic_service_detail', args=[service.slug])
        self.assertContains(self.client.get(self.url), url)
        response = self.client.get(url)
        self.assertContains(response, 'Возьмите документы питомца')
        self.assertContains(response, '&lt;script&gt;')
        self.assertContains(response, 'Стоимость уточняется')
        service.is_published = False
        service.save(update_fields=['is_published'])
        self.assertEqual(self.client.get(url).status_code, 404)
