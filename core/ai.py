"""
Claude API wrapper for supplier risk scoring.
All AI calls flow through this module — views and services never import anthropic directly.
"""
import json
import re
from dataclasses import dataclass

import anthropic
from django.conf import settings

RISK_SCORE_SYSTEM = """
Você é um analista sênior de risco em procurement de um grande varejista digital brasileiro.
Recebe dados de fornecedores e retorna uma avaliação estruturada de risco.
Responda APENAS com JSON válido, sem texto fora do objeto JSON.
""".strip()

RISK_SCORE_USER_TEMPLATE = """
Avalie o risco de procurement do fornecedor abaixo.

Fornecedor: {nome}
CNPJ: {cnpj}
Categoria: {categoria}
Cotações recentes: {resumo_cotacoes}

Responda com exatamente este JSON:
{{
  "score": <float de 0.0 a 10.0, onde 10 = risco máximo>,
  "nivel_risco": <"BAIXO" | "MÉDIO" | "ALTO" | "CRÍTICO">,
  "resumo": "<2-3 frases em português para o comprador>",
  "principais_riscos": ["<risco 1>", "<risco 2>"],
  "acoes_recomendadas": ["<ação 1>", "<ação 2>"]
}}
"""


@dataclass
class RiskScoreResult:
    score: float
    nivel_risco: str
    resumo: str
    principais_riscos: list
    acoes_recomendadas: list


def _parse_result(text: str) -> RiskScoreResult:
    cleaned = re.sub(r"```json|```", "", text).strip()
    data = json.loads(cleaned)
    return RiskScoreResult(
        score=float(data["score"]),
        nivel_risco=data["nivel_risco"],
        resumo=data["resumo"],
        principais_riscos=data.get("principais_riscos", []),
        acoes_recomendadas=data.get("acoes_recomendadas", []),
    )


def compute_risk_score(nome: str, cnpj: str, categoria: str, resumo_cotacoes: str = "Sem cotações ainda.") -> RiskScoreResult:
    """
    Calls Claude to generate a risk score for a supplier.
    Returns a RiskScoreResult dataclass.
    Raises ValueError if the API key is not configured.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY não configurada. Adicione no arquivo .env.")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    user_prompt = RISK_SCORE_USER_TEMPLATE.format(
        nome=nome,
        cnpj=cnpj,
        categoria=categoria,
        resumo_cotacoes=resumo_cotacoes,
    )

    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=1024,
        system=RISK_SCORE_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return _parse_result(response.content[0].text)
