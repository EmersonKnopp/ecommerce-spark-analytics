"""Camada GOLD: tabela fato pronta para análise + execução das queries SQL."""
import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.config import DATA_GOLD, DATA_SILVER, REPORTS_DIR, REVENUE_STATUS, SQL_DIR


def build_fact_sales(orders: DataFrame, items: DataFrame, products: DataFrame, customers: DataFrame) -> DataFrame:
    """Uma linha por item vendido, já enriquecida com cliente, produto e receita."""
    return (
        items.join(orders, "order_id")
        .join(F.broadcast(products), "product_id")
        .join(F.broadcast(customers), "customer_id")
        .where(F.col("status").isin(REVENUE_STATUS))
        .select(
            "order_id",
            "order_date",
            F.date_format("order_date", "yyyy-MM").alias("order_month"),
            F.year("order_date").alias("order_year"),
            "customer_id",
            "state",
            "product_id",
            "product_name",
            "category",
            "quantity",
            "unit_price",
            F.round(F.col("quantity") * F.col("unit_price"), 2).alias("revenue"),
        )
    )


def run_sql_reports(spark: SparkSession) -> None:
    """Executa cada arquivo .sql da pasta sql/ e salva o resultado em CSV."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        query = sql_file.read_text(encoding="utf-8").strip().rstrip(";")
        result = spark.sql(query)
        print(f"\n[sql] {sql_file.name}")
        result.show(10, truncate=False)
        result.toPandas().to_csv(REPORTS_DIR / f"{sql_file.stem}.csv", index=False)


def run(spark: SparkSession) -> None:
    read = lambda n: spark.read.parquet(str(DATA_SILVER / n))  # noqa: E731
    fact = build_fact_sales(read("orders"), read("order_items"), read("products"), read("customers"))

    fact.write.mode("overwrite").partitionBy("order_year").parquet(str(DATA_GOLD / "fact_sales"))
    print(f"[gold] fact_sales: {fact.count():,} linhas")

    spark.read.parquet(str(DATA_GOLD / "fact_sales")).createOrReplaceTempView("fact_sales")
    run_sql_reports(spark)
