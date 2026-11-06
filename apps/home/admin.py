from django.contrib import admin

from .models import ClientShowcase, ContactSettings, TeamMember, ClinicService


@admin.register(ClientShowcase)
class ClientShowcaseAdmin(admin.ModelAdmin):
    list_display = ("name", "project_title", "has_video_review", "sort_order", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("name", "vehicle", "rutube_url")

    @admin.display(description="Изделие или проект", ordering="vehicle")
    def project_title(self, obj):
        return obj.vehicle

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "vehicle" and field is not None:
            field.label = "Изделие или проект"
            field.widget.attrs["placeholder"] = "Например, кухня или шкаф для прихожей"
        return field

    @admin.display(boolean=True, description="Видеоотзыв")
    def has_video_review(self, obj):
        return bool(obj.rutube_url)
    list_editable = ("sort_order", "is_published")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "sort_order", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("name", "position")
    list_editable = ("sort_order", "is_published")


@admin.register(ContactSettings)
class ContactSettingsAdmin(admin.ModelAdmin):
    list_display = ("phone_primary", "address", "is_published", "updated_at")

    def has_add_permission(self, request):
        return not ContactSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClinicService)
class ClinicServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "price", "price_from", "sort_order", "is_published")
    list_filter = ("is_published", "group")
    search_fields = ("name", "group", "summary")
    list_editable = ("sort_order", "is_published")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "group", "summary")}),
        ("Стоимость", {"fields": ("price", "price_from", "price_note")}),
        ("Подробности", {"fields": ("description", "preparation"), "classes": ("collapse",)}),
        ("Публикация", {"fields": ("sort_order", "is_published")}),
    )
