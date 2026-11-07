"""Public phone for the clinic's shared layout."""
from django import template
from django.conf import settings

from .furniture_contacts import furniture_contacts, phone_link

register = template.Library()


@register.simple_tag(takes_context=True)
def clinic_phone(context):
    if settings.VET_CLINIC_USE_ADMIN_CONTACTS:
        phones = context.get("clinic_phones")
        if phones is not None:
            return next(iter(phones), None)
        return furniture_contacts(context).get("primary")
    return phone_link(settings.VET_CLINIC_PHONE)
