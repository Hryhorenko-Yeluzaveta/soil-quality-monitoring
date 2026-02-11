from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Crop(models.Model):
    TYPE_CHOICES = [
        ('Berries', 'Ягоди'),
        ('Fruits', 'Фруктові'),
        ('Cereals', 'Зернові'),
        ('Vegetables', 'Овочеві'),
        ('Forage', 'Кормові')
    ]
    category = models.CharField(choices=TYPE_CHOICES, max_length=20, default='Vegetables')
    name = models.CharField(max_length=50, verbose_name="Назва культури")
    image = models.ImageField(blank=True, upload_to="crops", verbose_name="Зображення")
    min_humidity = models.FloatField(
        verbose_name="Мін. вологість",
        help_text="в %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    max_humidity = models.FloatField(
        verbose_name="Макс. вологість",
        help_text="в %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
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
        validators=[MinValueValidator(0.0), MaxValueValidator(14.0)]
    )
    max_ph = models.FloatField(
        verbose_name="Макс. pH",
        validators=[MinValueValidator(0.0), MaxValueValidator(14.0)]
    )
    min_nitrogen = models.FloatField(
        verbose_name="Мін. вміст азоту",
        help_text="мг/кг",
        validators = [MinValueValidator(0.0)]
    )
    max_nitrogen = models.FloatField(
        verbose_name="Макс. вміст азоту",
        help_text="мг/кг",
        validators = [MinValueValidator(0.0)]
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Культура"
        verbose_name_plural = "Культури"

class Sector(models.Model):
    name = models.CharField(max_length=50, verbose_name="Назва сектору")
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True)
    x_start = models.FloatField(
        help_text="у %",
        validators = [MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    y_start = models.FloatField(
        help_text="у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    height = models.FloatField(
        help_text="у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    width = models.FloatField(
        help_text="у %",
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
    TYPE_CHOICES = [
        ('TEMP', 'Температура'),
        ('HUM', 'Вологість'),
        ('PH', 'Кислотність'),
        ('NIT', 'Азот')
    ]
    type = models.CharField(
        max_length=5,
        choices=TYPE_CHOICES
    )
    serial_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Format: SF-type-number"
    )
    offset_x = models.FloatField(
        help_text="у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    offset_y = models.FloatField(
        help_text="у %",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    is_active = models.BooleanField(default=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="sensors")

    def __str__(self):
        return self.serial_number

    class Meta:
        verbose_name = "Сенсор",
        verbose_name_plural = "Сенсори"

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