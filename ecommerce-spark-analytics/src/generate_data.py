"""Gera um dataset sintético de e-commerce, propositalmente "sujo".

Os problemas injetados (duplicatas, nulos, datas inválidas, quantidades negativas,
pedidos órfãos, caixa inconsistente) existem para a camada silver ter o que limpar.
"""
import argparse

import numpy as np
import pandas as pd

from src.config import DATA_RAW

STATES = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE", "CE", "GO"]
STATE_WEIGHTS = [0.30, 0.14, 0.12, 0.07, 0.07, 0.06, 0.06, 0.05, 0.04, 0.09]

CATALOG = {
    "Eletrônicos": [("Fone Bluetooth", 189.90), ("Smartwatch", 459.00), ("Carregador Turbo", 79.90), ("Caixa de Som", 299.00)],
    "Casa": [("Jogo de Panelas", 349.00), ("Air Fryer", 429.90), ("Aspirador Robô", 899.00), ("Kit Organizadores", 69.90)],
    "Moda": [("Tênis Casual", 259.90), ("Jaqueta Jeans", 219.00), ("Mochila", 139.90), ("Camiseta Básica", 49.90)],
    "Livros": [("Python para Dados", 89.90), ("SQL na Prática", 74.90), ("Estatística Descomplicada", 99.00), ("Big Data com Spark", 129.90)],
    "Esportes": [("Bola de Futebol", 99.90), ("Tapete de Yoga", 89.00), ("Halteres 10kg", 159.90), ("Garrafa Térmica", 59.90)],
}

HORIZON_END = np.datetime64("2025-06-30")


def build_tables(n_customers: int, n_orders: int, seed: int):
    rng = np.random.default_rng(seed)

    # ---- clientes
    customer_ids = np.arange(1, n_customers + 1)
    signup_days = rng.integers(0, 546, n_customers)
    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "name": [f"Cliente {i:05d}" for i in customer_ids],
            "state": rng.choice(STATES, n_customers, p=STATE_WEIGHTS),
            "signup_date": pd.Timestamp("2023-01-01") + pd.to_timedelta(signup_days, unit="D"),
        }
    )

    # ---- produtos
    rows, pid = [], 1
    for category, items in CATALOG.items():
        for name, price in items:
            rows.append((pid, name, category, price))
            pid += 1
    products = pd.DataFrame(rows, columns=["product_id", "product_name", "category", "price"])

    # ---- pedidos (poucos clientes compram muito: distribuição de Pareto)
    weights = rng.pareto(2.0, n_customers) + 1
    weights = weights / weights.sum()
    order_ids = np.arange(1, n_orders + 1)
    order_customers = rng.choice(customer_ids, n_orders, p=weights)

    signup = customers.set_index("customer_id")["signup_date"].loc[order_customers].to_numpy()
    available_days = (HORIZON_END - signup).astype("timedelta64[D]").astype(int)
    offsets = (rng.random(n_orders) * (available_days + 1)).astype(int)
    order_dates = signup + offsets.astype("timedelta64[D]")

    orders = pd.DataFrame(
        {
            "order_id": order_ids,
            "customer_id": order_customers,
            "order_date": pd.Series(order_dates).dt.strftime("%Y-%m-%d"),
            "status": rng.choice(
                ["created", "paid", "shipped", "delivered", "cancelled"],
                n_orders,
                p=[0.03, 0.07, 0.10, 0.75, 0.05],
            ),
        }
    )

    # ---- itens de pedido
    n_items = rng.integers(1, 5, n_orders)
    item_order_ids = np.repeat(order_ids, n_items)
    total = item_order_ids.size
    popularity = rng.pareto(1.5, len(products)) + 1
    popularity = popularity / popularity.sum()
    item_products = rng.choice(products["product_id"].to_numpy(), total, p=popularity)
    base_price = products.set_index("product_id")["price"].loc[item_products].to_numpy()
    order_items = pd.DataFrame(
        {
            "order_item_id": np.arange(1, total + 1),
            "order_id": item_order_ids,
            "product_id": item_products,
            "quantity": rng.integers(1, 4, total),
            "unit_price": np.round(base_price * rng.uniform(0.90, 1.05, total), 2),
        }
    )

    customers["signup_date"] = customers["signup_date"].dt.strftime("%Y-%m-%d")
    return customers, products, orders, order_items, rng


def inject_noise(customers, orders, order_items, rng, seed):
    """Suja os dados para simular uma fonte real."""
    # clientes: estado com caixa/espaços errados, estado nulo, linhas duplicadas
    idx = rng.choice(len(customers), int(len(customers) * 0.05), replace=False)
    customers.loc[idx, "state"] = customers.loc[idx, "state"].str.lower() + " "
    idx = rng.choice(len(customers), int(len(customers) * 0.02), replace=False)
    customers.loc[idx, "state"] = None
    customers = pd.concat([customers, customers.sample(frac=0.01, random_state=seed)], ignore_index=True)

    # pedidos: data inválida, status com caixa errada, cliente inexistente, duplicatas
    idx = rng.choice(len(orders), int(len(orders) * 0.003), replace=False)
    orders.loc[idx, "order_date"] = "data-invalida"
    idx = rng.choice(len(orders), int(len(orders) * 0.03), replace=False)
    orders.loc[idx, "status"] = orders.loc[idx, "status"].str.upper()
    idx = rng.choice(len(orders), int(len(orders) * 0.002), replace=False)
    orders.loc[idx, "customer_id"] = 999999
    orders = pd.concat([orders, orders.sample(frac=0.005, random_state=seed)], ignore_index=True)

    # itens: quantidade negativa e preço nulo
    idx = rng.choice(len(order_items), int(len(order_items) * 0.005), replace=False)
    order_items.loc[idx, "quantity"] = order_items.loc[idx, "quantity"] * -1
    order_items["unit_price"] = order_items["unit_price"].astype(float)
    idx = rng.choice(len(order_items), int(len(order_items) * 0.003), replace=False)
    order_items.loc[idx, "unit_price"] = np.nan

    return customers, orders, order_items


def main():
    parser = argparse.ArgumentParser(description="Gera dados sintéticos de e-commerce.")
    parser.add_argument("--customers", type=int, default=5000)
    parser.add_argument("--orders", type=int, default=40000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    customers, products, orders, order_items, rng = build_tables(args.customers, args.orders, args.seed)
    customers, orders, order_items = inject_noise(customers, orders, order_items, rng, args.seed)

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    for name, df in [("customers", customers), ("products", products), ("orders", orders), ("order_items", order_items)]:
        df.to_csv(DATA_RAW / f"{name}.csv", index=False)
        print(f"[generate] {name}: {len(df):,} linhas -> data/raw/{name}.csv")


if __name__ == "__main__":
    main()
