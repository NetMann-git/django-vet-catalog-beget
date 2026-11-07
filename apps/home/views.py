# apps/home/views.py

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .vet_context import VetHomeContextBuilder


def home(request):
    context = VetHomeContextBuilder.build(request)
    return render(request, "home/home.html", context)


def services(request):
    from .service_catalog import service_context
    return render(request, "home/services.html", service_context(request))


def service_detail(request, slug):
    from .models import ClinicService

    service = get_object_or_404(ClinicService, slug=slug, is_published=True)
    return render(request, "home/service_detail.html", {"service": service})


def materials(request):
    return render(request, "home/materials.html")


def reviews(request):
    from django.core.paginator import Paginator
    from apps.reviews.models import Review

    published = (Review.objects.filter(is_published=True, product__is_active=True)
                 .select_related("product", "user", "reply")
                 .prefetch_related("images").order_by("-created_at", "-pk"))
    page = Paginator(published, 12).get_page(request.GET.get("page"))
    return render(request, "home/reviews.html", {"page_obj": page})


def about(request):
    return render(request, "home/about_workshop.html")


def contacts(request):
    from .templatetags.furniture_contacts import public_url

    return render(request, "home/contacts.html", {
        "clinic_address": settings.VET_CLINIC_ADDRESS.strip(),
        "clinic_hours": settings.VET_CLINIC_HOURS.strip(),
        "clinic_map_url": public_url(settings.VET_CLINIC_MAP_URL),
    })


def portfolio(request):
    from django.shortcuts import redirect
    from django.urls import reverse

    return redirect(reverse("home") + "#portfolio")
