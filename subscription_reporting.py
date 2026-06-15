from __future__ import annotations

from io import BytesIO
from pathlib import Path

import altair as alt
import pandas as pd

from subscription_agent import SUBSCRIPTION_COLUMNS, SUBSCRIPTION_FILE


def load_subscriptions(path: Path | str = SUBSCRIPTION_FILE) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame(columns=SUBSCRIPTION_COLUMNS)
    data = pd.read_excel(target, engine="openpyxl")
    for column in SUBSCRIPTION_COLUMNS:
        if column not in data.columns:
            data[column] = ""
    return data[SUBSCRIPTION_COLUMNS]


def compute_subscription_kpis(subscriptions: pd.DataFrame) -> dict[str, object]:
    if subscriptions is None or subscriptions.empty:
        return {
            "total": 0,
            "pending": 0,
            "validated": 0,
            "products": 0,
            "potential_revenue": "0",
        }

    prices = (
        subscriptions["Prix promotionnel"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.extract(r"(\d+(?:\.\d+)?)")[0]
    )
    potential_revenue = float(pd.to_numeric(prices, errors="coerce").fillna(0).sum())
    return {
        "total": int(len(subscriptions)),
        "pending": int((subscriptions["Statut"] == "En attente de validation").sum()),
        "validated": int((subscriptions["Statut"] == "Validée").sum()),
        "products": int(subscriptions["Produit"].nunique()),
        "potential_revenue": f"{potential_revenue:,.0f}".replace(",", " "),
    }


def build_subscription_charts(subscriptions: pd.DataFrame) -> dict[str, alt.Chart]:
    if subscriptions is None or subscriptions.empty:
        return {}

    data = subscriptions.copy()
    data["Date"] = pd.to_datetime(data["Date souscription"], errors="coerce").dt.date.astype(str)

    by_product = data.groupby("Produit", dropna=False).size().reset_index(name="Souscriptions")
    by_status = data.groupby("Statut", dropna=False).size().reset_index(name="Souscriptions")
    by_category = data.groupby("Catégorie produit", dropna=False).size().reset_index(name="Souscriptions")
    by_date = data.groupby("Date", dropna=False).size().reset_index(name="Souscriptions")

    return {
        "product": alt.Chart(by_product).mark_bar(cornerRadius=4, color="#0b8ff0").encode(
            x=alt.X("Souscriptions:Q", title="Souscriptions"),
            y=alt.Y("Produit:N", title=None, sort="-x"),
            tooltip=["Produit:N", "Souscriptions:Q"],
        ),
        "status": alt.Chart(by_status).mark_bar(cornerRadius=4, color="#0c2347").encode(
            x=alt.X("Statut:N", title=None),
            y=alt.Y("Souscriptions:Q", title="Souscriptions"),
            tooltip=["Statut:N", "Souscriptions:Q"],
        ),
        "date": alt.Chart(by_date).mark_line(point=True, color="#0b8ff0").encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Souscriptions:Q", title="Souscriptions"),
            tooltip=["Date:T", "Souscriptions:Q"],
        ),
        "category": alt.Chart(by_category).mark_arc(innerRadius=45).encode(
            theta=alt.Theta("Souscriptions:Q"),
            color=alt.Color("Catégorie produit:N", title="Catégorie"),
            tooltip=["Catégorie produit:N", "Souscriptions:Q"],
        ),
    }


def export_subscriptions(subscriptions: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        subscriptions.to_excel(writer, index=False, sheet_name="Souscriptions")
    return output.getvalue()
