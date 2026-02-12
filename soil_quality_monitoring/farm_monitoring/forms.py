from django import forms

from .models import Crop


class CropForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data.get('name')
        qs = Crop.objects.filter(name__iexact=name)
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