"""Configurações centrais do projeto: caminhos e regras de negócio."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_BRONZE = ROOT / "data" / "bronze"
DATA_SILVER = ROOT / "data" / "silver"
DATA_GOLD = ROOT / "data" / "gold"

SQL_DIR = ROOT / "sql"
REPORTS_DIR = ROOT / "output" / "reports"
IMAGES_DIR = ROOT / "docs" / "images"

# Status válidos de pedido e quais deles contam como receita
VALID_STATUS = ["created", "paid", "shipped", "delivered", "cancelled"]
REVENUE_STATUS = ["paid", "shipped", "delivered"]
