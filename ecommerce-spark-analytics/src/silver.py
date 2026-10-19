"""Camada SILVER: limpeza, tipagem e integridade referencial.

As funções clean_* são puras (DataFrame -> DataFrame), o que facilita testar.
"""
import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.config import DATA_BRONZE, DATA_SILVER, REPORTS_DIR, VALID_STATUS


def clean_customers(df: DataFrame) -> DataFrame:
    state = F.upper(F.trim(F.col("state")))
    return (
        df.withColumn("customer_id", F.col("customer_id").cast("int"))
        .withColumn("name", F.trim(F.col("name")))
        .withColumn("state", F.when(state.isNull() | (state == ""), F.lit("ND")).otherwise(state))
        .withColumn("signup_date", F.to_date(F.col("signup_date"), "yyyy-MM-dd"))
        .filter(F.col("customer_id").isNotNull())
        .dropDuplicates(["customer_id"])
        .select("customer_id", "name", "state", "signup_date")
    )


def clean_products(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("product_id", F.col("product_id").cast("int"))
        .withColumn("product_name", F.trim(F.col("product_name")))
        .withColumn("category", F.trim(F.col("category")))
        .withColumn("price", F.col("price").cast("double"))
        .filter(F.col("product_id").isNotNull() & (F.col("price") > 0))
        .dropDuplicates(["product_id"])
        .select("product_id", "product_name", "category", "price")
    )


def clean_orders(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("order_id", F.col("order_id").cast("int"))
        .withColumn("customer_id", F.col("customer_id").cast("int"))
        .withColumn("order_date", F.to_date(F.col("order_date"), "yyyy-MM-dd"))
        .withColumn("status", F.lower(F.trim(F.col("status"))))
        .filter(
            F.col("order_id").isNotNull()
            & F.col("customer_id").isNotNull()
            & F.col("order_date").isNotNull()
            & F.col("status").isin(VALID_STATUS)
        )
        .dropDuplicates(["order_id"])
        .select("order_id", "customer_id", "order_date", "status")
    )


def clean_order_items(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("order_item_id", F.col("order_item_id").cast("int"))
        .withColumn("order_id", F.col("order_id").cast("int"))
        .withColumn("product_id", F.col("product_id").cast("int"))
        .withColumn("quantity", F.col("quantity").cast("int"))
        .withColumn("unit_price", F.col("unit_price").cast("double"))
        .filter(
            F.col("order_item_id").isNotNull()
            & F.col("order_id").isNotNull()
            & F.col("product_id").isNotNull()
            & (F.col("quantity") > 0)
            & (F.col("unit_price") > 0)
        )
        .dropDuplicates(["order_item_id"])
        .select("order_item_id", "order_id", "product_id", "quantity", "unit_price")
    )


def enforce_integrity(customers, products, orders, items):
    """Remove registros órfãos usando left_semi join (mantém só quem tem pai)."""
    orders = orders.join(customers.select("customer_id"), "customer_id", "left_semi")
    items = items.join(orders.select("order_id"), "order_id", "left_semi").join(
        products.select("product_id"), "product_id", "left_semi"
    )
    return orders, items


def run(spark: SparkSession) -> None:
    raw = {n: spark.read.parquet(str(DATA_BRONZE / n)) for n in ["customers", "products", "orders", "order_items"]}

    customers = clean_customers(raw["customers"])
    products = clean_products(raw["products"])
    orders = clean_orders(raw["orders"])
    items = clean_order_items(raw["order_items"])
    orders, items = enforce_integrity(customers, products, orders, items)

    silver = {"customers": customers, "products": products, "orders": orders, "order_items": items}

    quality = []
    for name, df in silver.items():
        df.write.mode("overwrite").parquet(str(DATA_SILVER / name))
        bronze_rows, silver_rows = raw[name].count(), df.count()
        quality.append(
            {
                "table": name,
                "bronze_rows": bronze_rows,
                "silver_rows": silver_rows,
                "discarded_rows": bronze_rows - silver_rows,
                "discarded_pct": round(100 * (bronze_rows - silver_rows) / bronze_rows, 2),
            }
        )
        print(f"[silver] {name}: {bronze_rows:,} -> {silver_rows:,} linhas")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(quality).to_csv(REPORTS_DIR / "data_quality.csv", index=False)
