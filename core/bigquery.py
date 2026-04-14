"""
BigQuery integration for market price lookups.

Architecture:
  - get_market_price() is the single public interface for all app code.
  - BQ_USE_SIMULATOR=True (default) → BigQuerySimulator (no GCP credentials needed).
  - BQ_USE_SIMULATOR=False → real google.cloud.bigquery.Client against GCP_PROJECT_ID.

This pattern lets you swap to production BigQuery by changing one .env variable,
with zero changes to app code — demonstrating Data Mesh / layered data architecture.

Production BQ table assumed: `{project}.procurement.market_prices`
Schema: produto STRING, categoria STRING, avg_price FLOAT64, updated_date DATE
"""
from django.conf import settings

# ---------------------------------------------------------------------------
# Production SQL (documented here, executed only when BQ_USE_SIMULATOR=False)
# ---------------------------------------------------------------------------
MARKET_PRICE_QUERY = """
SELECT
    avg_price,
    updated_date,
    'procurement.market_prices' AS fonte_bq
FROM `{project}.procurement.market_prices`
WHERE LOWER(produto) = LOWER(@produto)
  AND LOWER(categoria) = LOWER(@categoria)
ORDER BY updated_date DESC
LIMIT 1
"""

# ---------------------------------------------------------------------------
# Simulator — realistic seeded data, deterministic per (produto, categoria)
# ---------------------------------------------------------------------------
_SEED_PRICES: dict[str, dict[str, float]] = {
    "Eletrônicos": {
        "tv 55": 2840.00,
        "notebook": 3200.00,
        "smartphone": 1850.00,
        "tablet": 1400.00,
        "fone bluetooth": 320.00,
        "default": 1500.00,
    },
    "Moda": {
        "camiseta": 45.00,
        "tênis": 280.00,
        "jaqueta": 190.00,
        "calça jeans": 120.00,
        "default": 100.00,
    },
    "Alimentos": {
        "café 500g": 32.00,
        "azeite 500ml": 28.00,
        "whey protein": 180.00,
        "default": 25.00,
    },
    "Casa": {
        "aspirador": 450.00,
        "liquidificador": 150.00,
        "panela pressão": 120.00,
        "default": 200.00,
    },
    "Beleza": {
        "perfume": 210.00,
        "hidratante": 55.00,
        "default": 80.00,
    },
    "Esportes": {
        "bicicleta": 1200.00,
        "haltere": 95.00,
        "default": 300.00,
    },
}


class BigQuerySimulator:
    """
    In-memory simulation of a BigQuery market price table.
    Returns deterministic prices per (produto, categoria) so demos are reproducible.
    """

    def get_market_price(self, produto: str, categoria: str) -> dict:
        category_prices = _SEED_PRICES.get(categoria, {})
        produto_lower = produto.lower()

        price = None
        for key, value in category_prices.items():
            if key != "default" and key in produto_lower:
                price = value
                break
        if price is None:
            price = category_prices.get("default", 500.00)

        import datetime
        return {
            "avg_price": price,
            "updated_date": datetime.date.today().isoformat(),
            "fonte_bq": "simulator.procurement.market_prices",
        }


class BigQueryClient:
    """Thin wrapper over google.cloud.bigquery for production use."""

    def __init__(self):
        from google.cloud import bigquery
        self._client = bigquery.Client(project=settings.GCP_PROJECT_ID)

    def get_market_price(self, produto: str, categoria: str) -> dict:
        from google.cloud import bigquery

        query = MARKET_PRICE_QUERY.format(project=settings.GCP_PROJECT_ID)
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("produto", "STRING", produto),
                bigquery.ScalarQueryParameter("categoria", "STRING", categoria),
            ]
        )
        rows = list(self._client.query(query, job_config=job_config).result())
        if not rows:
            return {"avg_price": None, "updated_date": None, "fonte_bq": "procurement.market_prices"}
        row = rows[0]
        return {
            "avg_price": float(row.avg_price),
            "updated_date": str(row.updated_date),
            "fonte_bq": row.fonte_bq,
        }


def get_market_price(produto: str, categoria: str) -> dict:
    """
    Public interface. Returns:
      {avg_price: float | None, updated_date: str, fonte_bq: str}
    """
    if settings.BQ_USE_SIMULATOR:
        return BigQuerySimulator().get_market_price(produto, categoria)
    return BigQueryClient().get_market_price(produto, categoria)
