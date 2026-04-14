from django import forms
from .models import PriceQuote


class PriceQuoteForm(forms.ModelForm):
    class Meta:
        model = PriceQuote
        fields = ["produto", "preco_ofertado", "moeda", "data"]
        widgets = {
            "produto": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex: TV 55, Notebook, Tênis Running",
            }),
            "preco_ofertado": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "0,00",
            }),
            "moeda": forms.Select(attrs={"class": "form-select"}),
            "data": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
