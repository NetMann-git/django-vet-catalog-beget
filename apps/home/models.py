from django.db import models
from django.core.validators import MinValueValidator


class ClientShowcase(models.Model):
    """Карточка клиента для секции «Наши клиенты» на главной странице."""

    name = models.CharField(max_length=120, verbose_name="Имя клиента")
    vehicle = models.CharField(max_length=180, verbose_name="Автомобиль")
    image = models.ImageField(
        upload_to="home/clients/%Y/%m/",
        blank=True,
        verbose_name="Фотография",
    )
    # Kept in sync with historical migrations; public images use the image field.
    legacy_image = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        verbose_name="Старое статическое изображение",
    )
    rutube_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Ссылка на видеоотзыв Rutube",
        help_text="Оставьте пустым, если клиент не записывал видеоотзыв.",
    )
    sort_order = models.PositiveIntegerField(
        default=100,
        db_index=True,
        verbose_name="Порядок вывода",
        help_text="Чем меньше число, тем раньше карточка показывается.",
    )
    is_published = models.BooleanField(default=True, db_index=True, verbose_name="Опубликован")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменён")

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "Клиент на главной"
        verbose_name_plural = "Клиенты на главной"

    def __str__(self):
        return f"{self.name} — {self.vehicle}"

    @property
    def has_image(self):
        return bool(self.image)

    @property
    def rutube_embed_url(self):
        """Возвращает только проверенную embed-ссылку Rutube."""
        if not self.rutube_url:
            return ""

        import re
        from urllib.parse import urlparse

        try:
            parsed = urlparse(self.rutube_url)
        except (TypeError, ValueError):
            return ""

        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"rutube.ru", "www.rutube.ru"}:
            return ""

        match = re.search(r"/(?:video|play/embed)/([0-9a-fA-F]{32})(?:/|$)", parsed.path)
        if not match:
            return ""

        return f"https://rutube.ru/play/embed/{match.group(1).lower()}/"


class TeamMember(models.Model):
    """Сотрудник для секции «Наша команда» на главной странице."""

    name = models.CharField(max_length=120, verbose_name="Имя")
    position = models.CharField(max_length=180, verbose_name="Должность")
    image = models.ImageField(
        upload_to="home/team/%Y/%m/",
        blank=True,
        verbose_name="Фотография",
    )
    legacy_image = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        verbose_name="Старое статическое изображение",
    )
    sort_order = models.PositiveIntegerField(
        default=100,
        db_index=True,
        verbose_name="Порядок вывода",
        help_text="Чем меньше число, тем раньше сотрудник показывается.",
    )
    is_clinic_doctor = models.BooleanField(default=False, verbose_name="Врач клиники")
    is_published = models.BooleanField(default=True, db_index=True, verbose_name="Опубликован")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменён")

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "Сотрудник команды"
        verbose_name_plural = "Команда"

    def __str__(self):
        return f"{self.name} — {self.position}"

    @property
    def has_image(self):
        return bool(self.image)


class ContactSettings(models.Model):
    """Контактные данные для секции «Контакты» на главной странице."""

    phone_primary = models.CharField(max_length=40, verbose_name="Основной телефон")
    phone_secondary = models.CharField(max_length=40, blank=True, verbose_name="Дополнительный телефон")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    map_url = models.URLField(max_length=700, verbose_name="Ссылка на карту Яндекс")
    telegram_url = models.URLField(max_length=500, blank=True, verbose_name="Telegram")
    vk_url = models.URLField(max_length=500, blank=True, verbose_name="ВКонтакте")
    max_url = models.URLField(max_length=500, blank=True, verbose_name="MAX")
    is_published = models.BooleanField(default=True, verbose_name="Показывать секцию на главной")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменено")

    class Meta:
        verbose_name = "Контакты главной страницы"
        verbose_name_plural = "Контакты главной страницы"

    def __str__(self):
        return "Контакты главной страницы"


class ClinicService(models.Model):
    """Услуга клиники; отдельна от унаследованных товаров каталога."""
    name = models.CharField("Название услуги", max_length=180)
    slug = models.SlugField("Адресное имя", max_length=180, unique=True, allow_unicode=True)
    group = models.CharField("Направление", max_length=120, blank=True, db_index=True)
    summary = models.TextField("Краткое описание", blank=True)
    description = models.TextField("Описание", blank=True)
    preparation = models.TextField("Подготовка к визиту", blank=True)
    price = models.DecimalField("Стоимость, ₽", max_digits=10, decimal_places=2,
                                null=True, blank=True, validators=[MinValueValidator(0)])
    price_from = models.BooleanField("Стоимость от указанной суммы", default=False)
    price_note = models.CharField("Пояснение к стоимости", max_length=250, blank=True)
    sort_order = models.PositiveIntegerField("Порядок вывода", default=100, db_index=True)
    is_published = models.BooleanField("Опубликовано", default=False, db_index=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    class Meta:
        ordering = ("sort_order", "name", "pk")
        verbose_name = "Услуга клиники"
        verbose_name_plural = "Услуги клиники"

    def __str__(self):
        return self.name
