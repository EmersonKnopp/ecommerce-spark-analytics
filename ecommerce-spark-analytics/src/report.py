"""Gera gráficos a partir dos CSVs produzidos pelas queries SQL."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.config import IMAGES_DIR, REPORTS_DIR  # noqa: E402


def plot_monthly_revenue() -> None:
    df = pd.read_csv(REPORTS_DIR / "01_revenue_monthly.csv")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["order_month"], df["revenue"], marker="o", linewidth=1.5)
    ax.set_title("Receita mensal")
    ax.set_ylabel("R$")
    ax.set_xticks(range(0, len(df), 3))
    ax.set_xticklabels(df["order_month"].iloc[::3], rotation=45)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "receita_mensal.png", dpi=150)
    plt.close(fig)


def plot_rfm_segments() -> None:
    df = pd.read_csv(REPORTS_DIR / "03_rfm.csv")
    counts = df["segment"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(counts.index, counts.values)
    ax.set_title("Clientes por segmento RFM")
    ax.set_ylabel("Clientes")
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "segmentos_rfm.png", dpi=150)
    plt.close(fig)


def plot_cohort_heatmap() -> None:
    df = pd.read_csv(REPORTS_DIR / "04_cohort_retention.csv")
    pivot = df.pivot(index="cohort", columns="month_index", values="retention_pct")
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(pivot.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Meses desde a primeira compra")
    ax.set_ylabel("Coorte")
    ax.set_title("Retenção por coorte (%)")
    fig.colorbar(im, label="Retenção (%)")
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "retencao_coortes.png", dpi=150)
    plt.close(fig)


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    plot_monthly_revenue()
    plot_rfm_segments()
    plot_cohort_heatmap()
    print(f"[report] gráficos salvos em {IMAGES_DIR}")


if __name__ == "__main__":
    main()
