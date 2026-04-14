from django.contrib import admin
from .models import PriceQuote


@admin.register(PriceQuote)
class PriceQuoteAdmin(admin.ModelAdmin):
    list_display = ["produto", "supplier", "preco_ofertado", "preco_mercado", "margem_pct", "moeda", "data", "fonte_bq"]
    list_filter = ["moeda", "data"]
    search_fields = ["produto", "supplier__nome"]
    readonly_fields = ["id", "preco_mercado", "margem_pct", "fonte_bq", "created_at"]
