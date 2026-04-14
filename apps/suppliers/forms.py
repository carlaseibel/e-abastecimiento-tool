from django import forms
from .models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["nome", "cnpj", "categoria"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do fornecedor"}),
            "cnpj": forms.TextInput(attrs={"class": "form-control", "placeholder": "00.000.000/0001-00"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
        }


class CSVUploadForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo CSV",
        help_text="Colunas esperadas: nome, cnpj, categoria",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )
