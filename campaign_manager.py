from __future__ import annotations

from io import BytesIO

import pandas as pd


def campaign_offer_label(offer_config: dict[str, object]) -> str:
    standard = offer_config.get("standard_price", "")
    promo = offer_config.get("promo_price", "")
    start = offer_config.get("start_date", "")
    end = offer_config.get("end_date", "")
    if standard or promo:
        return f"Standard {standard} | Promo {promo} | {start} - {end}"
    return "Offre à définir"


def report_to_excel_bytes(report: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        report.to_excel(writer, index=False, sheet_name="Campagne")
    return output.getvalue()
