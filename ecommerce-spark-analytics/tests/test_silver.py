from src.silver import clean_customers, clean_order_items, clean_orders


def test_clean_customers_normaliza_estado_e_remove_duplicados(spark):
    df = spark.createDataFrame(
        [
            ("1", "Ana", " sp ", "2023-01-10"),
            ("1", "Ana", "SP", "2023-01-10"),
            ("2", "Bia", None, "2023-02-01"),
        ],
        ["customer_id", "name", "state", "signup_date"],
    )
    result = {r["customer_id"]: r["state"] for r in clean_customers(df).collect()}
    assert result == {1: "SP", 2: "ND"}


def test_clean_orders_descarta_data_invalida_status_invalido_e_duplicata(spark):
    df = spark.createDataFrame(
        [
            ("1", "10", "2024-01-05", "Delivered"),
            ("1", "10", "2024-01-05", "delivered"),
            ("2", "10", "data-invalida", "paid"),
            ("3", "10", "2024-01-06", "desconhecido"),
        ],
        ["order_id", "customer_id", "order_date", "status"],
    )
    rows = clean_orders(df).collect()
    assert [(r["order_id"], r["status"]) for r in rows] == [(1, "delivered")]


def test_clean_order_items_descarta_quantidade_negativa_e_preco_nulo(spark):
    df = spark.createDataFrame(
        [
            ("1", "1", "5", "2", "10.5"),
            ("2", "1", "5", "-1", "10.5"),
            ("3", "1", "5", "1", None),
        ],
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    )
    rows = clean_order_items(df).collect()
    assert [r["order_item_id"] for r in rows] == [1]
