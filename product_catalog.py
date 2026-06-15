from __future__ import annotations

import pandas as pd


CATALOG_REQUIRED_COLUMNS = [
    "Code produit",
    "Nom produit",
    "Colonne source bddf2",
    "Catégorie",
    "Description",
    "Conditions d’éligibilité",
    "Avantages",
    "Limites / points de vigilance",
    "Arguments commerciaux",
    "Mots-clés chatbot",
]


def clean_product_name(product_name: str) -> str:
    return str(product_name).replace("Produit -", "").strip()


def get_product_icon(product_name: str, category: str | None = None) -> str:
    name = f"{category or ''} {clean_product_name(product_name)}".lower()
    if any(token in name for token in ["carte", "card", "visa", "mastercard"]):
        return "💳"
    if any(token in name for token in ["crédit", "credit", "prêt", "pret", "loan", "financement"]):
        return "🏦"
    if any(token in name for token in ["assurance", "insurance", "protection"]):
        return "🛡️"
    if any(token in name for token in ["épargne", "epargne", "saving", "livret"]):
        return "💰"
    if any(token in name for token in ["invest", "bourse", "placement", "fund", "fonds"]):
        return "📈"
    if any(token in name for token in ["digital", "mobile", "app", "web", "internet"]):
        return "📱"
    if any(token in name for token in ["pack", "package"]):
        return "✨"
    if any(token in name for token in ["compte", "account"]):
        return "🧾"
    return "✨"


def validate_catalog(catalog: pd.DataFrame) -> list[str]:
    return [column for column in CATALOG_REQUIRED_COLUMNS if column not in catalog.columns]


def normalize_source_column(value: object) -> str:
    return str(value).strip()


def prepare_catalog(catalog: pd.DataFrame) -> pd.DataFrame:
    prepared = catalog.copy()
    for column in CATALOG_REQUIRED_COLUMNS:
        if column in prepared.columns:
            prepared[column] = prepared[column].fillna("").astype(str).str.strip()
    return prepared


def get_catalog_product(catalog: pd.DataFrame | None, source_column: str) -> dict[str, object] | None:
    if catalog is None or catalog.empty:
        return None
    source = normalize_source_column(source_column)
    matches = catalog[catalog["Colonne source bddf2"].map(normalize_source_column) == source]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()


def split_catalog_field(value: object) -> list[str]:
    text = "" if pd.isna(value) else str(value).strip()
    if not text:
        return []
    separators = ["\n", ";", "|", "•"]
    items = [text]
    for separator in separators:
        if separator in text:
            items = [item.strip(" -•\t") for item in text.split(separator)]
            break
    return [item for item in items if item]


def first_catalog_value(catalog_product: dict[str, object] | None, candidates: list[str], default: str = "") -> str:
    if not catalog_product:
        return default
    for column in candidates:
        value = catalog_product.get(column)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def get_catalog_offer_fields(catalog_product: dict[str, object] | None) -> dict[str, str]:
    return {
        "standard_price": first_catalog_value(
            catalog_product,
            ["Prix standard", "Prix standard du produit", "Tarif standard", "Frais"],
            "À définir",
        ),
        "promo_price": first_catalog_value(
            catalog_product,
            ["Prix promotionnel", "Prix promo", "Tarif promotionnel", "Offre promotionnelle"],
            "Aucune promotion",
        ),
        "fees": first_catalog_value(catalog_product, ["Frais éventuels", "Frais", "Tarification"], ""),
        "duration": first_catalog_value(catalog_product, ["Durée", "Durée contrat", "Engagement"], ""),
    }


def catalog_display_name(product_name: str, catalog_product: dict[str, object] | None = None) -> str:
    if catalog_product and catalog_product.get("Nom produit"):
        return str(catalog_product["Nom produit"])
    return clean_product_name(product_name)


def get_product_description(product_name: str, catalog_product: dict[str, object] | None = None) -> str:
    if catalog_product and catalog_product.get("Description"):
        return str(catalog_product["Description"])
    clean_name = clean_product_name(product_name)
    return (
        f"{clean_name} est une offre bancaire proposée au client lorsque son profil, son comportement "
        "et les usages observés dans son cluster suggèrent une opportunité commerciale pertinente."
    )


def get_product_details(
    product_name: str,
    score: float,
    cluster_label: str,
    catalog_product: dict[str, object] | None = None,
) -> dict[str, object]:
    clean_name = catalog_display_name(product_name, catalog_product)
    category = str(catalog_product.get("Catégorie", "")) if catalog_product else ""
    return {
        "name": clean_name,
        "category": category,
        "description": get_product_description(product_name, catalog_product),
        "why": (
            f"Le produit ressort avec un score de {score:.1f}% auprès des clients similaires. "
            f"Le client appartient au segment {cluster_label}, ce qui indique une proximité avec "
            "des profils déjà équipés de cette offre."
        ),
        "eligibility": split_catalog_field(catalog_product.get("Conditions d’éligibilité", "")) if catalog_product else [],
        "benefits": split_catalog_field(catalog_product.get("Avantages", "")) if catalog_product else [
            "Renforce la relation client avec une proposition contextualisée.",
            "S'appuie sur les comportements observés dans le segment, pas sur une règle isolée.",
            "Permet au conseiller de prioriser les offres à plus fort potentiel.",
        ],
        "limits": split_catalog_field(catalog_product.get("Limites / points de vigilance", "")) if catalog_product else [
            "Le score indique une propension, pas une décision automatique.",
            "La recommandation doit être validée avec la situation réelle et les contraintes réglementaires.",
            "Les données produits doivent rester correctement codées en 0/1 pour fiabiliser le résultat.",
        ],
        "sales_arguments": split_catalog_field(catalog_product.get("Arguments commerciaux", "")) if catalog_product else [
            f"Positionner {clean_name} comme une offre cohérente avec les usages du client.",
            "Mettre en avant la comparaison avec les clients du même segment.",
            "Utiliser le score comme support de discussion, sans forcer la souscription.",
        ],
    }
