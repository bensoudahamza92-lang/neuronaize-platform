from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd


SUBSCRIPTION_FILE = Path(__file__).parent / "subscriptions.xlsx"
SUBSCRIPTION_COLUMNS = [
    "Subscription ID",
    "Date souscription",
    "Code Client",
    "Nom",
    "Prénom",
    "Produit",
    "Catégorie produit",
    "Score recommandation",
    "Prix standard",
    "Prix promotionnel",
    "Canal",
    "Statut",
    "Contrat généré",
    "Terms generated",
    "Validation finale",
    "Commentaire",
]

STATUS_DRAFT = "Brouillon"
STATUS_PENDING = "En attente de validation"
STATUS_VALIDATED = "Validée"
STATUS_REJECTED = "Rejetée"
STATUS_CONTRACT = "Contrat généré"


@dataclass
class SubscriptionSession:
    step: int
    code_client: str
    nom: str
    prenom: str
    product_name: str
    product_category: str
    score: float
    channel: str = "Email"
    status: str = STATUS_DRAFT


def initialize_subscription_session(
    client: dict[str, object],
    product: dict[str, object],
    score: float,
    channel: str = "Email",
) -> dict[str, object]:
    return asdict(
        SubscriptionSession(
            step=1,
            code_client=str(client.get("code_client", "")).strip(),
            nom=str(client.get("nom", "")).strip(),
            prenom=str(client.get("prenom", "")).strip(),
            product_name=str(product.get("name", "")).strip(),
            product_category=str(product.get("category", "")).strip(),
            score=float(score or 0),
            channel=channel,
        )
    )


def update_subscription_step(session: dict[str, object], step: int) -> dict[str, object]:
    updated = dict(session)
    updated["step"] = max(1, min(int(step), 5))
    return updated


def validate_client_identity(code_client: object, nom: object, prenom: object) -> tuple[bool, list[str]]:
    missing = []
    if not str(code_client or "").strip():
        missing.append("Code Client")
    if not str(nom or "").strip():
        missing.append("Nom")
    if not str(prenom or "").strip():
        missing.append("Prénom")
    return not missing, missing


def create_subscription_request(
    client: dict[str, object],
    product: dict[str, object],
    score: float,
    contract_markdown: str,
    terms_generated: bool = True,
    channel: str = "Email",
    status: str = STATUS_PENDING,
    comment: str = "",
) -> dict[str, object]:
    return {
        "Subscription ID": f"NZA-SUB-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
        "Date souscription": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Code Client": str(client.get("code_client", "")).strip(),
        "Nom": str(client.get("nom", "")).strip(),
        "Prénom": str(client.get("prenom", "")).strip(),
        "Produit": str(product.get("name", "")).strip(),
        "Catégorie produit": str(product.get("category", "")).strip(),
        "Score recommandation": float(score or 0),
        "Prix standard": str(product.get("standard_price", "À définir")),
        "Prix promotionnel": str(product.get("promo_price", "Aucune promotion")),
        "Canal": channel,
        "Statut": status,
        "Contrat généré": "Oui" if contract_markdown else "Non",
        "Terms generated": "Oui" if terms_generated else "Non",
        "Validation finale": "Non",
        "Commentaire": comment,
        "_contract_markdown": contract_markdown,
    }


def save_subscription_to_excel(
    subscription: dict[str, object],
    path: Path | str = SUBSCRIPTION_FILE,
) -> pd.DataFrame:
    target = Path(path)
    public_row = {column: subscription.get(column, "") for column in SUBSCRIPTION_COLUMNS}
    new_row = pd.DataFrame([public_row], columns=SUBSCRIPTION_COLUMNS)

    if target.exists():
        existing = pd.read_excel(target, engine="openpyxl")
        combined = pd.concat([existing, new_row], ignore_index=True)
    else:
        combined = new_row

    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        combined.to_excel(writer, index=False, sheet_name="Souscriptions")
    return combined


def get_subscription_status_badge(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == STATUS_VALIDATED.lower():
        return "badge-success"
    if normalized == STATUS_REJECTED.lower():
        return "badge-danger"
    if normalized in {STATUS_PENDING.lower(), STATUS_CONTRACT.lower()}:
        return "badge-warning"
    return "badge-neutral"
