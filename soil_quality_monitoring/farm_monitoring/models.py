from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Crop(models.Model):
    class Category(models.TextChoices):
        BERRIES = 'Berries', 'Ягоди'
        FRUITS = 'Fruits', 'Фрукти'
        GRAINS = 'Grains', 'Зернові'
        VEGETABLES = 'Vegetables', 'Овочі'
        FORAGE = 'Forage', 'Кормові'

    category = models.CharField(choices=Category.choices, max_length=50, default=Category.VEGETABLES, verbose_name="Категорія")
    name = models.CharField(max_length=50, verbose_name="Назва культури")
    image = models.ImageField(blank=True, upload_to="crops", verbose_name="Зображення")
    archived = models.BooleanField(default=False, verbose_name="Заархівовано")
    min_humidity = models.FloatField(
        verbose_name="Мін. вологість",
        help_text="в %",
        validators=[MinValueValidator(0.0, message="Не може бути менше 0."),
                    MaxValueValidator(100.0, message="Не може бути більше 100.")]
    )
    max_humidity = models.FloatField(
        verbose_name="Макс. вологість",
        help_text="в %",
        validators=[MinValueValidator(0.0, message="Не може бути менше 0."),
                    MaxValueValidator(100.0, message="Не може бути більше 100.")]
    )
    min_temperature = models.FloatField(
        verbose_name="Мін. температура",
        help_text="°C"
    )
    max_temperature = models.FloatField(
        verbose_name="Макс. температура",
        help_text="°C"
    )
    min_ph = models.FloatField(
        verbose_name="Мін. pH",
        validators=[MinValueValidator(0.0, message="Не може бути менше 0."),
                    MaxValueValidator(14.0, message="pH не може бути більше 14.")]
    )
    max_ph = models.FloatField(
        verbose_name="Макс. pH",
        validators=[MinValueValidator(0.0, message="Не може бути менше 0."),
                    MaxValueValidator(14.0, message="pH не може бути більше 14.")]
    )
    min_nitrogen = models.FloatField(
        verbose_name="Мін. вміст азоту",
        help_text="мг/кг",
        validators = [MinValueValidator(0.0, message="Не може бути менше 0.")]
    )
    max_nitrogen = models.FloatField(
        verbose_name="Макс. вміст азоту",
        help_text="мг/кг",
        validators = [MinValueValidator(0.0, message="Не може бути менше 0.")]
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Культура"
        verbose_name_plural = "Культури"

class Sector(models.Model):
    name = models.CharField(max_length=50, verbose_name="Назва сектору")
    crop = models.ForeignKey(
        'Crop',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Посіяна культура",
        related_name="sectors",
        limit_choices_to = {'archived': False}
    )
    archived = models.BooleanField(default=False, verbose_name="Заархівовано")
    x_start = models.FloatField(
        verbose_name="Позиція X",
        help_text="Зміщення зліва у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    y_start = models.FloatField(
        verbose_name="Позиція Y",
        help_text="Зміщення зверху у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    width = models.FloatField(
        verbose_name="Ширина",
        help_text="Ширина сектора у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    height = models.FloatField(
        verbose_name="Висота",
        help_text="Висота сектора у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    @property
    def area(self):
        return self.width * self.height

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Ділянка"
        verbose_name_plural = "Ділянки"

class Sensor(models.Model):
    class Type(models.TextChoices):
        TEMPERATURE = 'TEMP', 'Температура'
        HUMIDITY = 'HUM', 'Вологість'
        PH = 'PH', 'Кислотність'
        NITROGEN = ('NIT', 'Азот')

    type = models.CharField(
        max_length=5,
        choices=Type.choices,
        null=False,
        blank=False,
        verbose_name="Тип сенсора"
    )
    serial_number = models.CharField(
        max_length=20,
        help_text="Format: SF-type-number",
        verbose_name="Серійний номер сенсора"
    )
    offset_x = models.FloatField(
        help_text="у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Розташування за Х"
    )
    offset_y = models.FloatField(
        help_text="у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Розташування за Y"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активований")
    archived = models.BooleanField(default=False, verbose_name="Заархівовано")
    sector = models.ForeignKey(
        Sector,
        on_delete=models.CASCADE,
        related_name="sensors",
        verbose_name="Сектор",
        limit_choices_to = {'archived': False}
    )

    def __str__(self):
        return self.serial_number

    class Meta:
        verbose_name = "Сенсор",
        verbose_name_plural = "Сенсори"
        constraints = [
            models.UniqueConstraint(
                fields=['serial_number'],
                condition=models.Q(archived=False),
                name='unique_active_sensor_serial'
            )
        ]

class Measurement(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="measurements")
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["sensor", "timestamp"]),
        ]
        ordering = ["-timestamp"]
        verbose_name = "Показник"
        verbose_name_plural = "Показники"