from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["nome", "cnpj", "categoria", "score_risco", "nivel_risco", "scored_at", "created_at"]
    list_filter = ["categoria", "nivel_risco"]
    search_fields = ["nome", "cnpj"]
    readonly_fields = ["id", "score_risco", "nivel_risco", "resumo_ia", "scored_at", "created_at"]
