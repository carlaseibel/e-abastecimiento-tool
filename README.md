# e-Abastecimento Tool

Portal de procurement para negociação com fornecedores, desenvolvido em Django com integração de IA (Claude) e BigQuery.
<img width="1231" height="618" alt="Screenshot 2026-04-14 162049" src="https://github.com/user-attachments/assets/b94f8d26-b212-4f94-9e9a-5f1098a6f908" />

---

## Contexto

Projeto desenvolvido como portfólio para demonstrar competências em:

- **Python / Django** — modelagem de domínio, ORM, views baseadas em classes, formulários
- **Integração com IA** — score de risco de fornecedores via Claude API (Anthropic)
- **BigQuery / Google Cloud** — arquitetura com camada de abstração simulada, pronta para produção
- **Domínio de Procurement** — cotações, margem vs. mercado, classificação de risco

---

## Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| Cadastro de fornecedores | Manual ou via upload em lote (CSV) |
| Score de Risco com IA | Claude analisa o fornecedor e retorna score 0–10, nível e resumo em PT-BR |
| Cotações com preço de mercado | Ao registrar uma cotação, o sistema busca o preço de mercado no BigQuery e calcula a margem automaticamente |
| Dashboard | Visão geral de fornecedores ordenados por risco, com estatísticas agregadas |
| Admin Django | Gestão completa via `/admin/` |

---

## Arquitetura

```
e-abastecimiento-tool/
├── manage.py
├── requirements.txt
├── .env.example
│
├── config/
│   ├── settings.py       # Configurações (AI model, BQ mode, banco de dados)
│   └── urls.py           # Roteamento principal
│
├── core/                 # Infraestrutura desacoplada dos apps Django
│   ├── ai.py             # Wrapper Claude API — todas as chamadas de IA passam aqui
│   └── bigquery.py       # Interface BigQuery — simulador ou cliente real (via .env)
│
├── apps/
│   ├── suppliers/        # Fornecedores: modelo, upload CSV, scoring por IA
│   └── quotes/           # Cotações: modelo, busca de preço de mercado via BQ
│
└── templates/            # Bootstrap 5, HTML server-side
    ├── base.html
    ├── dashboard.html
    ├── suppliers/
    └── quotes/
```

### Decisões de design

**`core/` não é um app Django**
`core/ai.py` e `core/bigquery.py` não têm models, migrations nem URLs. São módulos Python puros de serviço — os apps Django importam deles, não o contrário.

**Separação entre apps**
`suppliers` e `quotes` têm responsabilidades distintas. `PriceQuote` referencia `Supplier` via FK, mas a lógica de negócio de cada domínio fica isolada no seu próprio `services.py`.

**BigQuery com interface intercambiável**
`core/bigquery.get_market_price()` é a única interface pública. Internamente, a variável `BQ_USE_SIMULATOR` decide se usa o `BigQuerySimulator` (dados realistas em memória) ou o `google.cloud.bigquery.Client` real. Trocar para produção exige apenas alterar o `.env`.

**IA como serviço, não na view**
As views nunca importam `anthropic` diretamente. O fluxo é: `view → suppliers/services.py → core/ai.py → Anthropic SDK`. Isso facilita mock em testes e troca de modelo.

---

## Modelos

### `Supplier`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Chave primária |
| `nome` | CharField | Nome do fornecedor |
| `cnpj` | CharField (único) | CNPJ |
| `categoria` | CharField (choices) | Eletrônicos, Moda, Alimentos, Casa, Beleza, Esportes |
| `score_risco` | DecimalField 0–10 | Preenchido pela IA |
| `nivel_risco` | CharField | BAIXO / MÉDIO / ALTO / CRÍTICO |
| `resumo_ia` | TextField | Resumo gerado pelo Claude em PT-BR |
| `scored_at` | DateTimeField | Data/hora do último scoring |

### `PriceQuote`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Chave primária |
| `supplier` | FK → Supplier | |
| `produto` | CharField | Nome/SKU do produto |
| `preco_ofertado` | DecimalField | Preço enviado pelo fornecedor |
| `preco_mercado` | DecimalField | Buscado no BigQuery automaticamente |
| `moeda` | CharField | BRL / USD |
| `data` | DateField | Data da cotação |
| `margem_pct` | DecimalField | `(mercado - ofertado) / mercado × 100` — calculado no `save()` |
| `fonte_bq` | CharField | Tabela/query do BigQuery utilizada |

---

## Integração com IA

O score de risco é calculado via **Claude** (`claude-sonnet-4-6`).

**Prompt enviado ao modelo:**
- Nome, CNPJ e categoria do fornecedor
- Resumo das últimas cotações (produto, preço ofertado vs. mercado, margem)

**Resposta estruturada (JSON):**
```json
{
  "score": 7.2,
  "nivel_risco": "ALTO",
  "resumo": "Fornecedor com histórico de...",
  "principais_riscos": ["Alta volatilidade de preço", "..."],
  "acoes_recomendadas": ["Solicitar contrato de preço fixo", "..."]
}
```

O parsing defensivo em `core/ai.py` remove code fences e valida o JSON antes de salvar.

---

## Integração com BigQuery

`core/bigquery.py` implementa dois backends com a mesma interface:

| Ambiente | Backend | Como ativar |
|---|---|---|
| Desenvolvimento / Demo | `BigQuerySimulator` | `BQ_USE_SIMULATOR=True` (padrão) |
| Produção | `google.cloud.bigquery.Client` | `BQ_USE_SIMULATOR=False` + `GCP_PROJECT_ID=...` |

O simulador usa preços semeados deterministicamente por categoria, então os dados do demo são reproduzíveis.

**Query de produção (documentada em `core/bigquery.py`):**
```sql
SELECT avg_price, updated_date
FROM `{project}.procurement.market_prices`
WHERE LOWER(produto) = LOWER(@produto)
  AND LOWER(categoria) = LOWER(@categoria)
ORDER BY updated_date DESC
LIMIT 1
```

---

## Como rodar

**Pré-requisitos:** Python 3.11+, pip

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env e adicione: ANTHROPIC_API_KEY=sk-ant-...

# 3. Criar banco de dados
python manage.py migrate

# 4. Criar superusuário (opcional, para /admin/)
python manage.py createsuperuser

# 5. Rodar servidor
python manage.py runserver
```

Acesse: [http://localhost:8000](http://localhost:8000)

---

## Fluxo de uso

1. **Importar fornecedores** em `/fornecedores/upload/` com CSV:
   ```
   nome,cnpj,categoria
   Fornecedor ABC,12.345.678/0001-99,Eletrônicos
   ```

2. **Calcular Score de Risco** na página do fornecedor → chama Claude e salva o resultado

3. **Registrar cotação** → sistema busca o preço de mercado no BigQuery e calcula a margem automaticamente

4. **Dashboard** em `/` mostra fornecedores ordenados por score de risco

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | — | Django secret key |
| `DEBUG` | `True` | Modo debug |
| `ANTHROPIC_API_KEY` | — | Chave da API Anthropic (obrigatório para IA) |
| `AI_MODEL` | `claude-sonnet-4-6` | Modelo Claude utilizado |
| `BQ_USE_SIMULATOR` | `True` | `False` para usar BigQuery real |
| `GCP_PROJECT_ID` | — | Project ID do GCP (necessário se BQ_USE_SIMULATOR=False) |

---

## Stack

- **Backend:** Python 3.11+ / Django 5.1
- **IA:** Anthropic Claude (`claude-sonnet-4-6`) via SDK oficial
- **Data:** BigQuery (Google Cloud) — simulado em dev, real em produção
- **Frontend:** Bootstrap 5 (server-side rendering)
- **Banco (dev):** SQLite — trocar para PostgreSQL em produção
