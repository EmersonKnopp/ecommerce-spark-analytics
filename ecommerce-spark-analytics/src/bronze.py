"""Camada BRONZE: ingestão do dado cru, sem transformar nada.

Tudo é lido como string (inferSchema desligado) para não perder informação.
Adicionamos apenas metadados de ingestão para rastreabilidade.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.config import DATA_BRONZE, DATA_RAW

TABLES = ["customers", "products", "orders", "order_items"]


def ingest_table(spark: SparkSession, name: str) -> DataFrame:
    df = spark.read.option("header", True).option("inferSchema", False).csv(str(DATA_RAW / f"{name}.csv"))
    return df.withColumn("_ingested_at", F.current_timestamp()).withColumn("_source_file", F.lit(f"{name}.csv"))


def run(spark: SparkSession) -> None:
    for name in TABLES:
        df = ingest_table(spark, name)
        df.write.mode("overwrite").parquet(str(DATA_BRONZE / name))
        print(f"[bronze] {name}: {df.count():,} linhas")
