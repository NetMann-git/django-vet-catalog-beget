"""Clinic shell: phone is explicitly configured, never inherited from seeded contacts."""
from django import template
from django.conf import settings
from .furniture_contacts import phone_link

register = template.Library()

@register.simple_tag
def clinic_phone():
    return phone_link(getattr(settings, "VET_CLINIC_PHONE", ""))
