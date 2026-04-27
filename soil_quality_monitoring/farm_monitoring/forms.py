import json

from django import forms
from shapely.geometry import Point, Polygon

from .models import Crop, Sensor, Sector, User


class CropCreateForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data.get('name')
        qs = Crop.objects.filter(name__iexact=name, archived=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Культура з такою назвою вже існує.")

        return name

    def clean(self):
        cleaned_data = super().clean()

        validation_pairs = [
            ('min_temperature', 'max_temperature', 'температура'),
            ('min_humidity', 'max_humidity', 'вологість'),
            ('min_ph', 'max_ph', 'кислотність'),
            ('min_nitrogen', 'max_nitrogen', 'вміст азоту'),
        ]

        for min_field, max_field, name in validation_pairs:
            min_val = cleaned_data.get(min_field)
            max_val = cleaned_data.get(max_field)

            if min_val is not None and max_val is not None:
                if min_val > max_val:
                    self.add_error(min_field, f"Мінімальна {name} не може бути вищою за максимальну.")
                elif min_val == max_val:
                    error_msg = f"Мін. та макс. {name} не можуть бути однаковими."
                    self.add_error(min_field, error_msg)
                    self.add_error(max_field, error_msg)

        return cleaned_data

    class Meta:
        model = Crop
        fields = '__all__'

        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наприклад: Полуниця'}),
            'image': forms.FileInput(attrs={'class': 'file-input-hidden', 'id': 'id_image'}),
        }

        numeric_fields = [
            'min_temperature', 'max_temperature',
            'min_humidity', 'max_humidity',
            'min_ph', 'max_ph',
            'min_nitrogen', 'max_nitrogen'
        ]

        for field in numeric_fields:
            widgets[field] = forms.NumberInput(attrs={'class': 'form-control small', 'step': '0.1'})

        error_messages = {
            'name': {
                'required': "Будь ласка, введіть назву культури.",
                'max_length': "Назва занадто довга.",
            },
            'image': {
                'invalid_image': "Файл має бути коректним зображенням.",
            }
        }

        common_errors = {
            'required': "Обов'язкове поле.",
            'invalid': "Введіть коректне число."
        }

        for field in numeric_fields:
            error_messages[field] = common_errors


class CropUpdateForm(forms.ModelForm):
    class Meta(CropCreateForm.Meta):
        pass

class SensorCreateForm(forms.ModelForm):
    def clean_serial_number(self):
        serial_number = self.cleaned_data.get('serial_number')

        qs = Sensor.objects.filter(serial_number__iexact=serial_number, archived=False)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Сенсор з таким серійним номером вже зареєстровано в системі.")

        return serial_number

    def clean(self):
        cleaned_data = super().clean()

        offset_x = cleaned_data.get('offset_x')
        offset_y = cleaned_data.get('offset_y')
        sector = cleaned_data.get('sector')
        is_active = cleaned_data.get('is_active')

        if offset_x is not None and (offset_x < 0 or offset_x > 100):
            self.add_error('offset_x', "Координата X має бути в межах від 0 до 100%.")

        if offset_y is not None and (offset_y < 0 or offset_y > 100):
            self.add_error('offset_y', "Координата Y має бути в межах від 0 до 100%.")

        if not sector and is_active:
            self.add_error('is_active',
                           "Сенсор не може бути активним без прив'язки до сектора. Вимкніть його або оберіть сектор.")

        if sector and offset_x is not None and offset_y is not None and sector.polygon_coords:
            poly = Polygon(sector.polygon_coords)
            point = Point(offset_x, offset_y)
            if poly.is_valid and not poly.contains(point) and not poly.touches(point):
                self.add_error(
                    'offset_x',
                    f"Сенсор має бути встановлений всередині сектора «{sector.name}». "
                    f"Натисніть на мапі в межах підсвіченого полігону."
                )

        return cleaned_data

    class Meta:
        model = Sensor
        fields = ['type', 'sector', 'serial_number', 'offset_x', 'offset_y', 'is_active']

        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'sector': forms.Select(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: SN-HUM-1'
            }),
            'offset_x': forms.HiddenInput(attrs={'id': 'id_offset_x'}),
            'offset_y': forms.HiddenInput(attrs={'id': 'id_offset_y'}),
            'is_active': forms.CheckboxInput(),
        }

        error_messages = {
            'type': {
                'required': "Будь ласка, оберіть тип сенсора.",
            },
            'serial_number': {
                'required': "Серійний номер є обов'язковим.",
                'max_length': "Серійний номер занадто довгий.",
            },
            'offset_x': {
                'required': "Натисніть на мапі, щоб встановити сенсор.",
                'invalid': "Введіть коректне число."
            },
            'offset_y': {
                'required': "Натисніть на мапі, щоб встановити сенсор.",
                'invalid': "Введіть коректне число."
            }
        }


class SensorUpdateForm(SensorCreateForm):
    class Meta(SensorCreateForm.Meta):
        pass

class SectorCreateForm(forms.ModelForm):
    polygon_coords = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'id_polygon_coords'}),
        required=True,
        error_messages={'required': "Намалюйте сектор на мапі."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.polygon_coords:
            self.fields['polygon_coords'].initial = json.dumps(self.instance.polygon_coords)

    def clean_name(self):
        name = self.cleaned_data.get('name')

        qs = Sector.objects.filter(name__iexact=name, archived=False)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ділянка з такою назвою вже існує.")

        return name

    def clean_polygon_coords(self):
        raw = self.cleaned_data.get('polygon_coords')
        if not raw:
            raise forms.ValidationError("Намалюйте сектор на мапі.")

        try:
            coords = json.loads(raw)
        except (TypeError, ValueError):
            raise forms.ValidationError("Некоректний формат координат полігону.")

        if not isinstance(coords, list) or len(coords) < 3:
            raise forms.ValidationError("Сектор повинен мати щонайменше 3 точки.")

        normalized = []
        for point in coords:
            if not (isinstance(point, (list, tuple)) and len(point) == 2):
                raise forms.ValidationError("Некоректний формат точки полігону.")
            try:
                x, y = float(point[0]), float(point[1])
            except (TypeError, ValueError):
                raise forms.ValidationError("Координати точки повинні бути числами.")
            if not (0 <= x <= 100 and 0 <= y <= 100):
                raise forms.ValidationError("Координати точки повинні бути від 0 до 100%.")
            normalized.append([x, y])

        return normalized

    def clean(self):
        cleaned_data = super().clean()
        coords = cleaned_data.get('polygon_coords')
        if not coords:
            return cleaned_data

        new_poly = Polygon(coords)
        if not new_poly.is_valid:
            self.add_error('polygon_coords', "Полігон не може перетинати самого себе.")
            return cleaned_data

        existing = Sector.objects.filter(archived=False)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        for other in existing:
            if not other.polygon_coords:
                continue
            other_poly = Polygon(other.polygon_coords)
            if not other_poly.is_valid:
                continue
            if new_poly.intersects(other_poly) and not new_poly.touches(other_poly):
                raise forms.ValidationError(
                    f"Помилка розміщення! Ця ділянка перетинається з існуючою ділянкою «{other.name}»."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.polygon_coords = self.cleaned_data['polygon_coords']
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Sector
        fields = ['name', 'crop', 'polygon_coords']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: Сектор А-1'
            }),
        }

        error_messages = {
            'name': {
                'required': "Будь ласка, введіть назву ділянки.",
                'max_length': "Назва занадто довга (максимум 50 символів).",
            },
        }

class SectorUpdateForm(SectorCreateForm):
    pass

class UserForm(forms.ModelForm):
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введіть пароль'}),
        required=False,
        error_messages = {
            'required': "Будь ласка, введіть пароль."
        }
    )
    password_confirm = forms.CharField(
        label='Підтвердження пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторіть пароль'}),
        required=False,
        error_messages={
            'required': "Будь ласка, підтвердіть пароль."
        }
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

        error_messages = {
            'username': {
                'unique': "Користувач з таким логіном вже існує.",
                'required': "Будь ласка, введіть логін.",
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password or password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Паролі не співпадають. Спробуйте ще раз.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user