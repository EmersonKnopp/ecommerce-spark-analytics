# Pipeline de Analytics de E-commerce com PySpark

Pipeline de dados ponta a ponta construído com **PySpark**, **Spark SQL** e **Python**, seguindo a **arquitetura medalhão** (bronze → silver → gold). O projeto ingere dados brutos e propositalmente "sujos", limpa e valida, modela uma tabela fato e responde perguntas de negócio com SQL analítico (window functions, RFM, retenção por coorte).

## Stack

| Tecnologia | Uso no projeto |
|---|---|
| **PySpark (DataFrame API)** | Ingestão, limpeza, joins, escrita em Parquet |
| **Spark SQL** | Queries analíticas em `sql/` (CTEs, window functions, NTILE, LAG) |
| **Python** | Geração de dados sintéticos, orquestração, gráficos, testes |
| **Pandas / Matplotlib** | Exportação de resultados e visualizações |
| **Pytest** | Testes unitários das regras de limpeza |

## Arquitetura

```
  data/raw (CSV)          data/bronze            data/silver              data/gold
 ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌───────────────────┐
 │ customers    │      │ dado cru em  │      │ tipado, limpo,  │      │ fact_sales        │
 │ products     │ ───▶ │ Parquet +    │ ───▶ │ deduplicado,    │ ───▶ │ (particionada por │
 │ orders       │      │ metadados de │      │ íntegro (FKs)   │      │  ano) + 5 queries │
 │ order_items  │      │ ingestão     │      │ + relatório de  │      │  SQL → CSV/gráfico│
 └──────────────┘      └──────────────┘      │ qualidade       │      └───────────────────┘
                                             └─────────────────┘
```

- **Bronze:** leitura de tudo como string, sem perder informação, com `_ingested_at` e `_source_file`.
- **Silver:** cast de tipos, padronização (`trim`, `upper`, `lower`), tratamento de nulos, remoção de duplicatas, descarte de registros inválidos e integridade referencial via `left_semi` join. Gera `output/reports/data_quality.csv` com quantas linhas foram descartadas por tabela.
- **Gold:** `fact_sales` (um registro por item vendido, com `revenue`), usando *broadcast join* nas dimensões pequenas e particionamento por ano.

## Problemas de qualidade tratados

O gerador injeta problemas realistas para a camada silver resolver: clientes duplicados, estados com caixa/espaço errados ou nulos, datas inválidas, status com caixa inconsistente, pedidos de clientes inexistentes, pedidos duplicados, quantidades negativas e preços nulos.

## Perguntas de negócio respondidas em SQL

| Arquivo | Pergunta | Técnicas |
|---|---|---|
| `01_revenue_monthly.sql` | Como evoluem receita, ticket médio e crescimento mensal? | CTE, `LAG` |
| `02_top_products_by_category.sql` | Quais os 3 produtos mais vendidos de cada categoria? | `RANK`, `PARTITION BY` |
| `03_rfm.sql` | Como segmentar clientes por recência, frequência e valor? | `NTILE`, `CASE`, `CROSS JOIN` |
| `04_cohort_retention.sql` | Que % dos clientes de cada coorte volta a comprar? | `DATE_TRUNC`, `MONTHS_BETWEEN` |
| `05_running_total_by_category.sql` | Receita acumulada e média móvel por categoria? | Window frames |

## Como executar

Requisitos: **Python 3.10+** e **Java 17 ou 21** (necessário para o Spark). No Windows, prefira WSL2.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows (WSL): mesmo comando
pip install -r requirements.txt

python -m src.generate_data        # gera os CSVs em data/raw (5 mil clientes, 40 mil pedidos)
python -m src.run_pipeline         # bronze -> silver -> gold + queries SQL
python -m src.report               # gera gráficos em docs/images
pytest                             # roda os testes
```

Parâmetros opcionais do gerador: `--customers`, `--orders`, `--seed`.

## Estrutura

```
├── src/
│   ├── config.py            # caminhos e regras de negócio
│   ├── spark_session.py     # SparkSession local
│   ├── generate_data.py     # dados sintéticos com sujeira injetada
│   ├── bronze.py            # ingestão
│   ├── silver.py            # limpeza e integridade
│   ├── gold.py              # tabela fato + execução das queries
│   ├── run_pipeline.py      # orquestração
│   └── report.py            # gráficos
├── sql/                     # queries analíticas em Spark SQL
├── tests/                   # testes das funções de limpeza
└── docs/images/             # gráficos gerados
```

## Resultados

Após rodar `python -m src.report`, os gráficos ficam em `docs/images/`:

![Receita mensal](docs/images/receita_mensal.png)
![Segmentos RFM](docs/images/segmentos_rfm.png)
![Retenção por coorte](docs/images/retencao_coortes.png)

## Decisões técnicas

- **Parquet** em todas as camadas: formato colunar, com schema embutido e compressão.
- **Funções puras de limpeza** (`clean_*`): DataFrame entra, DataFrame sai, o que permite testar sem depender de arquivos.
- **`spark.sql.ansi.enabled=false`**: datas inválidas viram `NULL` e são descartadas de forma explícita na silver, em vez de interromper o job.
- **Dados sintéticos com seed fixa**: o projeto é 100% reproduzível, sem depender de download.

## Próximos passos

- Trocar o dataset sintético por um dataset real (ex.: Olist, no Kaggle)
- Orquestração com Airflow ou Prefect
- Formato Delta Lake / Iceberg
- Dockerfile para rodar sem instalar Java
- CI com GitHub Actions rodando `pytest`
