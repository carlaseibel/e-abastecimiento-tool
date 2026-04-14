"""
Business logic for suppliers:
  - CSV parsing and bulk import
  - AI risk scoring orchestration
"""
import csv
import io
from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from core.ai import compute_risk_score
from .models import Supplier


@dataclass
class CSVImportResult:
    imported: int
    skipped: int
    errors: list[dict]


def import_suppliers_from_csv(file_obj) -> CSVImportResult:
    """
    Parses an uploaded CSV file and bulk-creates/updates Supplier records.
    Expected columns: nome, cnpj, categoria
    Returns a CSVImportResult with counts and row-level errors.
    """
    content = file_obj.read().decode("utf-8-sig")  # utf-8-sig handles Excel BOM
    reader = csv.DictReader(io.StringIO(content))

    imported = 0
    skipped = 0
    errors = []

    required_columns = {"nome", "cnpj", "categoria"}
    if not required_columns.issubset(set(reader.fieldnames or [])):
        return CSVImportResult(
            imported=0,
            skipped=0,
            errors=[{"row": 0, "error": f"Colunas obrigatórias ausentes: {required_columns}"}],
        )

    valid_categorias = {c[0] for c in Supplier.CATEGORIA_CHOICES}

    for i, row in enumerate(reader, start=2):
        nome = row.get("nome", "").strip()
        cnpj = row.get("cnpj", "").strip()
        categoria = row.get("categoria", "").strip()

        if not nome or not cnpj:
            errors.append({"row": i, "error": "nome e cnpj são obrigatórios"})
            skipped += 1
            continue

        if categoria not in valid_categorias:
            categoria = "Outros"

        _, created = Supplier.objects.update_or_create(
            cnpj=cnpj,
            defaults={"nome": nome, "categoria": categoria},
        )
        imported += 1

    return CSVImportResult(imported=imported, skipped=skipped, errors=errors)


def run_risk_scoring(supplier: Supplier) -> Supplier:
    """
    Calls Claude API to score a supplier and persists the result.
    Builds a brief quote summary to give the AI context if quotes exist.
    """
    quotes = supplier.quotes.order_by("-data")[:5]
    if quotes.exists():
        lines = []
        for q in quotes:
            lines.append(
                f"- {q.produto}: ofertado R${q.preco_ofertado}, mercado R${q.preco_mercado} "
                f"(margem {q.margem_pct:.1f}%)"
            )
        resumo_cotacoes = "\n".join(lines)
    else:
        resumo_cotacoes = "Sem cotações ainda."

    result = compute_risk_score(
        nome=supplier.nome,
        cnpj=supplier.cnpj,
        categoria=supplier.categoria,
        resumo_cotacoes=resumo_cotacoes,
    )

    supplier.score_risco = result.score
    supplier.nivel_risco = result.nivel_risco
    supplier.resumo_ia = result.resumo
    supplier.scored_at = timezone.now()
    supplier.save(update_fields=["score_risco", "nivel_risco", "resumo_ia", "scored_at"])

    return supplier
