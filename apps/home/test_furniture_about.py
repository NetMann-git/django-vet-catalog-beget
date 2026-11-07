from django.test import TestCase
from django.urls import reverse


class VetAboutTests(TestCase):
    def test_about_page_has_clinic_content_and_visit_links(self):
        response = self.client.get(reverse('furniture_about'))
        self.assertContains(response, '<h1 id="clinic-title">О клинике</h1>')
        self.assertContains(response, 'Как подготовиться к визиту')
        self.assertContains(response, f'href="{reverse("furniture_services")}"')
        self.assertContains(response, f'href="{reverse("home")}#callback"')
        self.assertNotContains(response, 'О мебельной мастерской')

    def test_about_page_is_linked_from_home_and_sitemap(self):
        target = reverse('furniture_about')
        self.assertContains(self.client.get('/'), f'href="{target}"')
        self.assertContains(self.client.get('/sitemap-pages.xml'), target)
