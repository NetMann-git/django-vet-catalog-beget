from django.test import TestCase
from django.urls import resolve, reverse

from apps.products.models import Product
from apps.reviews.models import Review


class ClinicReviewsTests(TestCase):
    def test_clinic_reviews_do_not_display_catalog_reviews(self):
        product = Product.objects.create(title="Шкаф", slug="review-case", price=100)
        Review.objects.create(product=product, rating=5, text="Отзыв о шкафе", is_published=True)
        response = self.client.get(reverse("furniture_reviews"))
        self.assertContains(response, "Отзывы о клинике")
        self.assertNotContains(response, "Отзыв о шкафе")
        self.assertNotContains(response, product.get_absolute_url())
        self.assertEqual(resolve(reverse("reviews:add_review", args=[product.pk])).url_name, "add_review")
