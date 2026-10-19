"""Orquestra o pipeline completo: bronze -> silver -> gold (+ relatórios SQL)."""
import time

from src import bronze, gold, silver
from src.spark_session import get_spark


def main() -> None:
    spark = get_spark()
    try:
        for name, stage in [("bronze", bronze), ("silver", silver), ("gold", gold)]:
            start = time.time()
            stage.run(spark)
            print(f"== {name} concluída em {time.time() - start:.1f}s ==")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
