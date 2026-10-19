"""Criação da SparkSession em modo local."""
from pyspark.sql import SparkSession


def get_spark(app_name: str = "ecommerce-analytics", shuffle_partitions: int = 8) -> SparkSession:
    return (
        SparkSession.builder.master("local[*]")
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        # Datas inválidas viram NULL (tratadas na camada silver) em vez de estourar erro
        .config("spark.sql.ansi.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
