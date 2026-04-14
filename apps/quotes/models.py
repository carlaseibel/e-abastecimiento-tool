import uuid
from django.db import models


class PriceQuote(models.Model):
    MOEDA_CHOICES = [
        ("BRL", "Real (BRL)"),
        ("USD", "Dólar (USD)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name="Fornecedor",
    )
    produto = models.CharField(max_length=255, verbose_name="Produto")
    preco_ofertado = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Preço Ofertado"
    )
    preco_mercado = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="Preço de Mercado (BigQuery)"
    )
    moeda = models.CharField(max_length=3, choices=MOEDA_CHOICES, default="BRL")
    data = models.DateField(verbose_name="Data da Cotação")
    margem_pct = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Margem (%)"
    )
    fonte_bq = models.CharField(
        max_length=100, blank=True,
        verbose_name="Fonte BigQuery",
        help_text="Tabela/query usada para obter o preço de mercado"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-created_at"]
        verbose_name = "Cotação"
        verbose_name_plural = "Cotações"

    def __str__(self):
        return f"{self.produto} — {self.supplier.nome} ({self.data})"

    def save(self, *args, **kwargs):
        if self.preco_mercado and self.preco_ofertado and self.preco_mercado > 0:
            self.margem_pct = (
                (self.preco_mercado - self.preco_ofertado) / self.preco_mercado * 100
            )
        super().save(*args, **kwargs)

    @property
    def margem_badge_class(self):
        if self.margem_pct is None:
            return "secondary"
        if self.margem_pct >= 15:
            return "success"
        if self.margem_pct >= 5:
            return "warning"
        return "danger"
