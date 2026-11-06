"""Список только опубликованных услуг; поиск учитывает кириллицу SQLite."""
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from .models import ClinicService


def service_context(request):
    query = request.GET.get("q", "").strip()[:200]
    group = request.GET.get("group", "").strip()[:120]
    published = ClinicService.objects.filter(is_published=True)
    groups = sorted(set(published.exclude(group="").values_list("group", flat=True)), key=str.casefold)
    services = published.filter(group=group) if group else published
    if query:
        if connection.vendor == "sqlite":
            needle = query.casefold()
            ids = [pk for pk, name, summary, category in services.values_list("pk", "name", "summary", "group")
                   if any(needle in value.casefold() for value in (name, summary, category))]
            services = services.filter(pk__in=ids)
        else:
            services = services.filter(Q(name__icontains=query) | Q(summary__icontains=query) | Q(group__icontains=query))
    page = Paginator(services, 12).get_page(request.GET.get("page"))
    filters = {key: value for key, value in (("q", query), ("group", group)) if value}
    prefix = urlencode(filters)
    return {"page_obj": page, "service_groups": groups, "search_query": query,
            "selected_group": group, "page_query": prefix + "&" if prefix else "",
            "has_services": published.exists()}
