from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.suppliers.models import Supplier
from .forms import PriceQuoteForm
from .services import create_quote_with_market_price


class PriceQuoteCreateView(View):
    template_name = "quotes/form.html"

    def get(self, request, supplier_pk):
        supplier = get_object_or_404(Supplier, pk=supplier_pk)
        form = PriceQuoteForm(initial={"data": __import__("datetime").date.today()})
        return render(request, self.template_name, {"form": form, "supplier": supplier})

    def post(self, request, supplier_pk):
        supplier = get_object_or_404(Supplier, pk=supplier_pk)
        form = PriceQuoteForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "supplier": supplier})

        quote = create_quote_with_market_price(
            supplier=supplier,
            produto=form.cleaned_data["produto"],
            preco_ofertado=form.cleaned_data["preco_ofertado"],
            moeda=form.cleaned_data["moeda"],
            data=form.cleaned_data["data"],
        )

        messages.success(
            request,
            f"Cotação salva. Preço de mercado (BigQuery): R$ {quote.preco_mercado:.2f} | "
            f"Margem: {quote.margem_pct:.1f}%"
            if quote.preco_mercado else "Cotação salva.",
        )
        return redirect("supplier_detail", pk=supplier_pk)
