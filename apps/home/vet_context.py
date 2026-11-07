"""Контекст главной клиники без унаследованных мебельных данных, шаг 4."""
from django.urls import reverse

from apps.appointments.forms import CallbackRequestForm


from .models import ClinicService, TeamMember


def published_clinic_doctors():
    return TeamMember.objects.filter(is_clinic_doctor=True, is_published=True)


class VetHomeContextBuilder:
    @staticmethod
    def build(request):
        service_slug = request.GET.get("service", "").strip()
        initial = {}
        if service_slug and len(service_slug) <= 180:
            name = ClinicService.objects.filter(
                slug=service_slug, is_published=True,
            ).values_list("name", flat=True).first()
            if name:
                initial["comment"] = f"Интересует услуга: {name}"
        form = CallbackRequestForm(initial=initial)
        for name, field in form.fields.items():
            field.widget.attrs["aria-describedby"] = f"callback-{name}-error"
        form.fields['phone'].widget.attrs.update({'placeholder': 'Ваш номер телефона'})
        form.fields['comment'].widget.attrs.update({
            'placeholder': 'Кто ваш питомец и когда вам удобно ответить на звонок',
            'rows': 4,
        })
        categories = (
            ("Приём врача", "intake"),
            ("Диагностика", "diagnosis"),
            ("Профилактика", "prevention"),
            ("Лечение", "treatment"),
        )
        groups = set(ClinicService.objects.filter(
            is_published=True, group__in=[label for label, _ in categories],
        ).values_list("group", flat=True))
        shortcuts = [
            {
                "label": label,
                "icon": f"home/images/approved/{icon}.png",
                "url": reverse("furniture_services", query={"group": label} if label in groups else None),
            }
            for label, icon in categories
        ]
        return {
            "callback_form": form,
            "service_shortcuts": shortcuts,
            "clinic_doctors": published_clinic_doctors(),
        }
