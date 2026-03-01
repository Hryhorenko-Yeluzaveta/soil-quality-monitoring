from django import forms

from .models import Crop, Sensor, Sector


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

        if offset_x is not None and (offset_x < 0 or offset_x > 100):
            self.add_error('offset_x', "Координата X має бути в межах від 0 до 100%.")

        if offset_y is not None and (offset_y < 0 or offset_y > 100):
            self.add_error('offset_y', "Координата Y має бути в межах від 0 до 100%.")

        return cleaned_data

    class Meta:
        model = Sensor
        fields = ['type', 'sector', 'serial_number', 'offset_x', 'offset_y', 'is_active']

        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'sector': forms.Select(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: SN-A1-2024'
            }),
            'offset_x': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'offset_y': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'is_active': forms.CheckboxInput(),
        }

        error_messages = {
            'type': {
                'required': "Будь ласка, оберіть тип сенсора.",
            },
            'sector': {
                'required': "Будь ласка, прив'яжіть сенсор до сектора.",
            },
            'serial_number': {
                'required': "Серійний номер є обов'язковим.",
                'max_length': "Серійний номер занадто довгий.",
            },
            'offset_x': {
                'required': "Вкажіть координату X.",
                'invalid': "Введіть коректне число."
            },
            'offset_y': {
                'required': "Вкажіть координату Y.",
                'invalid': "Введіть коректне число."
            }
        }


class SensorUpdateForm(SensorCreateForm):
    class Meta(SensorCreateForm.Meta):
        pass

class SectorCreateForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data.get('name')

        qs = Sector.objects.filter(name__iexact=name, archived=False)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ділянка з такою назвою вже існує.")

        return name

    def clean(self):
        cleaned_data = super().clean()

        x_start = cleaned_data.get('x_start')
        y_start = cleaned_data.get('y_start')
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')

        fields_to_check = {
            'x_start': 'Позиція X',
            'y_start': 'Позиція Y',
            'width': 'Ширина',
            'height': 'Висота'
        }

        for field, label in fields_to_check.items():
            val = cleaned_data.get(field)
            if val is not None and (val < 0 or val > 100):
                self.add_error(field, f"{label} має бути в межах від 0 до 100%.")

        if None in (x_start, y_start, width, height):
            return cleaned_data

        new_x_end = x_start + width
        new_y_end = y_start + height

        if new_x_end > 100:
            self.add_error('width', "Ділянка виходить за праву межу карти (X + Ширина > 100%).")

        if new_y_end > 100:
            self.add_error('height', "Ділянка виходить за нижню межу карти (Y + Висота > 100%).")

        existing_sectors = Sector.objects.filter(archived=False)

        if self.instance.pk:
            existing_sectors = existing_sectors.exclude(pk=self.instance.pk)

        for sector in existing_sectors:
            other_x_end = sector.x_start + sector.width
            other_y_end = sector.y_start + sector.height

            if (x_start < other_x_end and
                    new_x_end > sector.x_start and
                    y_start < other_y_end and
                    new_y_end > sector.y_start):
                raise forms.ValidationError(
                    f"Помилка розміщення! Ця ділянка перетинається з існуючою ділянкою «{sector.name}»."
                )

        return cleaned_data

    class Meta:
        model = Sector
        fields = ['name', 'crop', 'x_start', 'y_start', 'width', 'height']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: Сектор А-1'
            }),
            'x_start': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'y_start': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
        }

        error_messages = {
            'name': {
                'required': "Будь ласка, введіть назву ділянки.",
                'max_length': "Назва занадто довга (максимум 50 символів).",
            },
            'x_start': {
                'required': "Вкажіть початкову координату X.",
                'invalid': "Введіть коректне число."
            },
            'y_start': {
                'required': "Вкажіть початкову координату Y.",
                'invalid': "Введіть коректне число."
            },
            'width': {
                'required': "Вкажіть ширину ділянки.",
                'invalid': "Введіть коректне число."
            },
            'height': {
                'required': "Вкажіть висоту ділянки.",
                'invalid': "Введіть коректне число."
            }
        }

class SectorUpdateForm(SectorCreateForm):
    pass