from html import unescape
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.appointments.models import CallbackRequest
from .models import ClinicService, TeamMember


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MANAGER_EMAILS=["clinic@example.test"],
    TELEGRAM_BOT_TOKEN="", MAX_BOT_TOKEN="",
)
class ClinicLaunchTests(TestCase):
    def test_callback_from_service_and_doctor_reaches_admin_and_mail(self):
        service = ClinicService.objects.create(name="Тестовая услуга", slug="test", is_published=True)
        doctor = TeamMember.objects.create(name="Тестовый врач", position="Врач", is_clinic_doctor=True)
        staff = get_user_model().objects.create_superuser("launch-admin", password="test-only")
        admin = Client()
        admin.force_login(staff)
        visitor = Client(enforce_csrf_checks=True)

        for url, name in [
            (reverse("clinic_service_detail", args=[service.slug]), service.name),
            (reverse("clinic_doctor_detail", args=[doctor.pk]), doctor.name),
        ]:
            detail = visitor.get(url).content.decode()
            callback = unescape(re.search(r'href="([^"]+\?(?:doctor|service)=[^"]+#callback)"', detail)[1])
            form = visitor.get(callback)
            comment = form.context["callback_form"].initial["comment"]
            self.assertIn(name, comment)
            response = visitor.post(reverse("appointments:callback_submit"), {
                "phone": "+79001112233", "comment": comment,
                "csrfmiddlewaretoken": visitor.cookies["csrftoken"].value,
            }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertTrue(response.json()["success"])
            saved = CallbackRequest.objects.get(comment=comment)
            self.assertIn(comment, mail.outbox[-1].body)
            self.assertEqual(mail.outbox[-1].to, ["clinic@example.test"])
            admin_url = reverse("admin:appointments_callbackrequest_change", args=[saved.pk])
            self.assertContains(admin.get(admin_url), comment)
            self.assertEqual(visitor.get(admin_url).status_code, 302)

    def test_clinic_menu_searches_services_without_catalog_links(self):
        for route in ("home", "furniture_services", "clinic_doctors", "furniture_reviews", "furniture_contacts"):
            response = self.client.get(reverse(route))
            self.assertContains(response, 'action="/services/"')
            for path in ("/catalog/", "/materials/", "/portfolio/", "/wishlist/"):
                self.assertNotContains(response, f'href="{path}"')
