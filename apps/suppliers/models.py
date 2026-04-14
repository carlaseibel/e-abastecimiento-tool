import uuid
from django.db import models


class Supplier(models.Model):
    CATEGORIA_CHOICES = [
        ("Eletrônicos", "Eletrônicos"),
        ("Moda", "Moda"),
        ("Alimentos", "Alimentos"),
        ("Casa", "Casa"),
        ("Beleza", "Beleza"),
        ("Esportes", "Esportes"),
        ("Outros", "Outros"),
    ]

    NIVEL_RISCO_CHOICES = [
        ("BAIXO", "Baixo"),
        ("MÉDIO", "Médio"),
        ("ALTO", "Alto"),
        ("CRÍTICO", "Crítico"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, verbose_name="Nome")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoria")

    # AI risk scoring — null until first scoring run
    score_risco = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        verbose_name="Score de Risco (0–10)"
    )
    nivel_risco = models.CharField(
        max_length=10, choices=NIVEL_RISCO_CHOICES,
        null=True, blank=True, verbose_name="Nível de Risco"
    )
    resumo_ia = models.TextField(blank=True, verbose_name="Resumo da IA")
    scored_at = models.DateTimeField(null=True, blank=True, verbose_name="Último scoring")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score_risco", "nome"]
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return f"{self.nome} ({self.cnpj})"

    @property
    def score_badge_class(self):
        mapping = {
            "BAIXO": "success",
            "MÉDIO": "warning",
            "ALTO": "danger",
            "CRÍTICO": "dark",
        }
        return mapping.get(self.nivel_risco, "secondary")
