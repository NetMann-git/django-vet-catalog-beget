"""Шаг 4: новая главная не выдаёт данные прошлого проекта за данные клиники."""
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from apps.appointments.models import CallbackRequest
from .models import ContactSettings, TeamMember


class VetHomeTests(TestCase):
    def test_home_does_not_publish_inherited_contacts_or_staff(self):
        ContactSettings.objects.update_or_create(pk=1, defaults={
            'phone_primary': '+7 (988) 580-88-99', 'address': 'Адрес автокаталога',
            'map_url': 'https://example.com/map', 'is_published': True,
        })
        TeamMember.objects.create(name='Сотрудник мебельного каталога', position='Менеджер', is_published=True)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'С заботой о тех,')
        self.assertContains(response, 'home/images/approved/hero.png')
        self.assertNotContains(response, 'Адрес автокаталога')
        self.assertNotContains(response, 'Сотрудник мебельного каталога')
        self.assertNotContains(response, 'Например: шкаф в прихожую')
        self.assertNotContains(response, 'LUSTRID')
        self.assertTrue(TeamMember.objects.filter(name='Сотрудник мебельного каталога').exists())

    def test_home_uses_existing_callback_route(self):
        response = self.client.get('/')
        self.assertContains(response, 'action="' + reverse('appointments:callback_submit') + '"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'id="callback"')
        self.assertEqual(response.content.decode().count('search/js/search.js'), 1)

    @patch('apps.appointments.views._notify_saved_inquiry')
    def test_callback_submission_still_creates_request(self, notify):
        response = self.client.post(reverse('appointments:callback_submit'), {
            'name': 'Тест', 'phone': '+7 (900) 123-45-67',
            'comment': 'Вопрос о питомце', 'website': '',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('Заявка на обратный звонок принята', response.json()['message'])
        self.assertEqual(CallbackRequest.objects.filter(source='homepage', comment='Вопрос о питомце').count(), 1)
        notify.assert_called_once()

    def test_invalid_phone_and_csrf_do_not_create_request(self):
        endpoint = reverse('appointments:callback_submit')
        before = CallbackRequest.objects.count()
        response = self.client.post(endpoint, {'phone': '123'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.json()['errors'])
        self.assertEqual(Client(enforce_csrf_checks=True).post(endpoint, {'phone': '+7 (900) 123-45-67'}).status_code, 403)
        self.assertEqual(CallbackRequest.objects.count(), before)

    def test_admin_contacts_and_active_schedule_on_both_pages(self):
        from datetime import time
        from apps.appointments.models import WorkingHours

        ContactSettings.objects.update_or_create(pk=1, defaults={
            "address": "Адрес клиники для теста",
            "phone_primary": "+7 (900) 111-22-33",
            "phone_secondary": "",
            "map_url": "https://example.com/clinic",
            "is_published": True,
        })
        WorkingHours.objects.update_or_create(day_of_week=0, defaults={
            "start_time": time(9), "end_time": time(18), "is_active": True,
        })
        WorkingHours.objects.update_or_create(day_of_week=6, defaults={
            "start_time": time(10), "end_time": time(14), "is_active": False,
        })
        with self.settings(VET_CLINIC_USE_ADMIN_CONTACTS=True):
            for url in (reverse("home"), reverse("furniture_contacts")):
                response = self.client.get(url)
                self.assertContains(response, "Адрес клиники для теста")
                self.assertContains(response, "tel:+79001112233")
                self.assertContains(response, "https://example.com/clinic")
                self.assertContains(response, "Понедельник: 09:00–18:00")
                self.assertNotContains(response, "Воскресенье")

    def test_service_shortcuts_filter_only_published_groups(self):
        from .models import ClinicService

        ClinicService.objects.create(name="УЗИ", slug="uzi", group="Диагностика", is_published=True)
        ClinicService.objects.create(name="Вакцинация", slug="vaccine", group="Профилактика")
        response = self.client.get(reverse("home"))
        shortcuts = {item["label"]: item["url"] for item in response.context["service_shortcuts"]}
        self.assertEqual(shortcuts["Диагностика"], reverse("furniture_services", query={"group": "Диагностика"}))
        self.assertEqual(shortcuts["Профилактика"], reverse("furniture_services"))

    def test_callback_prefills_comment_only_for_published_service(self):
        from .models import ClinicService

        service = ClinicService.objects.create(
            name="УЗИ питомца", slug="узи", is_published=True,
        )
        url = reverse("home", query={"service": service.slug}, fragment="callback")
        detail = self.client.get(reverse("clinic_service_detail", args=[service.slug]))
        self.assertContains(detail, f'href="{url}"')
        self.assertContains(self.client.get(url), "Интересует услуга: УЗИ питомца")

        service.is_published = False
        service.save(update_fields=["is_published"])
        self.assertNotContains(self.client.get(url), "УЗИ питомца")

    def test_only_published_clinic_doctors_are_listed(self):
        TeamMember.objects.create(name="Врач ВетАссист", position="Терапевт", is_clinic_doctor=True)
        TeamMember.objects.create(name="Черновик врача", position="Терапевт", is_clinic_doctor=True, is_published=False)
        TeamMember.objects.create(name="Старая команда", position="Менеджер")

        for route in ("home", "clinic_doctors"):
            response = self.client.get(reverse(route))
            self.assertContains(response, "Врач ВетАссист")
            self.assertNotContains(response, "Черновик врача")
            self.assertNotContains(response, "Старая команда")
