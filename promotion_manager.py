from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd


PROMOTIONS_FILE = Path(__file__).parent / "promotions.xlsx"
PROMOTION_COLUMNS = [
    "Colonne source bddf2",
    "Nom produit",
    "Prix standard",
    "Prix promotionnel",
    "Date début",
    "Date fin",
    "Message promotionnel",
    "Campagne active",
]


def empty_promotions() -> pd.DataFrame:
    return pd.DataFrame(columns=PROMOTION_COLUMNS)


def load_promotions(path: Path | str = PROMOTIONS_FILE) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return empty_promotions()
    data = pd.read_excel(target, engine="openpyxl")
    for column in PROMOTION_COLUMNS:
        if column not in data.columns:
            data[column] = ""
    return data[PROMOTION_COLUMNS]


def prepare_promotions(data: pd.DataFrame | None) -> pd.DataFrame:
    if data is None or data.empty:
        return empty_promotions()
    prepared = data.copy()
    for column in PROMOTION_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = ""
    prepared = prepared[PROMOTION_COLUMNS]
    text_columns = [column for column in PROMOTION_COLUMNS if column != "Campagne active"]
    for column in text_columns:
        prepared[column] = prepared[column].fillna("").astype(str).str.strip()
    prepared["Campagne active"] = prepared["Campagne active"].map(_active_flag)
    return prepared


def upsert_promotion(promotions: pd.DataFrame, promotion: dict[str, object]) -> pd.DataFrame:
    prepared = prepare_promotions(promotions)
    row = {column: promotion.get(column, "") for column in PROMOTION_COLUMNS}
    row["Campagne active"] = _active_flag(row.get("Campagne active", True))
    source_column = str(row["Colonne source bddf2"]).strip()
    if not source_column:
        return prepared

    remaining = prepared[prepared["Colonne source bddf2"].astype(str).str.strip() != source_column]
    return pd.concat([remaining, pd.DataFrame([row])], ignore_index=True)[PROMOTION_COLUMNS]


def save_promotions(promotions: pd.DataFrame, path: Path | str = PROMOTIONS_FILE) -> pd.DataFrame:
    prepared = prepare_promotions(promotions)
    target = Path(path)
    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        prepared.to_excel(writer, index=False, sheet_name="Promotions")
    return prepared


def export_promotions(promotions: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        prepare_promotions(promotions).to_excel(writer, index=False, sheet_name="Promotions")
    return output.getvalue()


def get_active_promotion(promotions: pd.DataFrame | None, product_source_column: str) -> dict[str, object] | None:
    prepared = prepare_promotions(promotions)
    if prepared.empty:
        return None
    mask = (
        prepared["Colonne source bddf2"].astype(str).str.strip() == str(product_source_column).strip()
    ) & prepared["Campagne active"]
    if not mask.any():
        return None
    return prepared[mask].iloc[0].to_dict()


def promotion_to_offer_config(promotion: dict[str, object] | None, default_offer: dict[str, object]) -> dict[str, object]:
    if not promotion:
        return default_offer
    return {
        "standard_price": promotion.get("Prix standard") or default_offer.get("standard_price", ""),
        "promo_price": promotion.get("Prix promotionnel") or default_offer.get("promo_price", ""),
        "start_date": promotion.get("Date début") or default_offer.get("start_date", ""),
        "end_date": promotion.get("Date fin") or default_offer.get("end_date", ""),
        "promo_message": promotion.get("Message promotionnel") or default_offer.get("promo_message", ""),
    }


def _active_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"", "1", "true", "vrai", "oui", "yes", "active", "actif"}
