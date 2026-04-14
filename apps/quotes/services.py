"""
Orchestrates BigQuery market price lookup when saving a PriceQuote.
"""
from core.bigquery import get_market_price
from .models import PriceQuote


def create_quote_with_market_price(supplier, produto: str, preco_ofertado, moeda: str, data) -> PriceQuote:
    """
    1. Fetches market price from BigQuery (or simulator).
    2. Creates and saves a PriceQuote — margem_pct is auto-calculated in model.save().
    """
    bq_data = get_market_price(produto=produto, categoria=supplier.categoria)

    quote = PriceQuote(
        supplier=supplier,
        produto=produto,
        preco_ofertado=preco_ofertado,
        preco_mercado=bq_data.get("avg_price"),
        moeda=moeda,
        data=data,
        fonte_bq=bq_data.get("fonte_bq", ""),
    )
    quote.save()
    return quote
