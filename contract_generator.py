from __future__ import annotations

from datetime import datetime
from uuid import uuid4


def generate_contract_id(prefix: str = "NZA-CONTRACT") -> str:
    """Generate a readable simulated contract identifier."""

    stamp = datetime.now().strftime("%Y%m%d")
    suffix = uuid4().hex[:8].upper()
    return f"{prefix}-{stamp}-{suffix}"


def _as_text(value: object, default: str = "Non renseigné") -> str:
    text = "" if value is None else str(value).strip()
    return text or default


def generate_contract(
    client: dict[str, object],
    product: dict[str, object],
    offer: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a simulated banking subscription contract payload."""

    offer = offer or {}
    contract_id = generate_contract_id()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    return {
        "contract_id": contract_id,
        "generated_at": generated_at,
        "client_code": _as_text(client.get("code_client")),
        "last_name": _as_text(client.get("nom")),
        "first_name": _as_text(client.get("prenom")),
        "product_name": _as_text(product.get("name")),
        "product_category": _as_text(product.get("category")),
        "standard_price": _as_text(offer.get("standard_price") or product.get("standard_price"), "À définir"),
        "promo_price": _as_text(offer.get("promo_price") or product.get("promo_price"), "Aucune promotion"),
        "main_conditions": product.get("eligibility") or ["Validation finale par la banque requise."],
        "benefits": product.get("benefits") or ["Offre proposée sur la base des clients similaires."],
        "bank_validation_clause": (
            "Cette souscription est une simulation de démonstration et nécessite une validation bancaire finale."
        ),
        "client_signature": f"Signature client simulée - {_as_text(client.get('prenom'))} {_as_text(client.get('nom'))}",
        "bank_signature": "Signature banque simulée - NeuronAIze Demo",
    }


def generate_terms_and_conditions(product: dict[str, object]) -> dict[str, object]:
    """Build simulated terms and conditions from catalogue product fields."""

    return {
        "description": _as_text(product.get("description")),
        "eligibility": product.get("eligibility") or ["Conditions d'éligibilité à confirmer par la banque."],
        "fees": _as_text(product.get("fees"), "Frais éventuels selon la grille tarifaire bancaire en vigueur."),
        "duration": _as_text(product.get("duration"), "Durée indicative selon le contrat produit."),
        "withdrawal_rights": (
            "Droits de rétractation simulés, à confirmer selon le cadre réglementaire applicable."
        ),
        "customer_responsibilities": (
            "Le client confirme l'exactitude des informations transmises et prend connaissance des conditions."
        ),
        "bank_responsibilities": (
            "La banque vérifie l'éligibilité, la conformité et la validation opérationnelle avant activation."
        ),
        "limits": product.get("limits") or ["Points de vigilance à compléter par la banque."],
        "compliance_clause": (
            "Clause conformité simulée : aucune souscription réelle n'est finalisée par ce démonstrateur."
        ),
    }


def format_contract_as_markdown(contract: dict[str, object], terms: dict[str, object]) -> str:
    """Return a presentation-ready markdown version of the simulated contract."""

    condition_lines = "\n".join(f"- {item}" for item in contract.get("main_conditions", []))
    benefit_lines = "\n".join(f"- {item}" for item in contract.get("benefits", []))
    terms_eligibility = "\n".join(f"- {item}" for item in terms.get("eligibility", []))
    terms_limits = "\n".join(f"- {item}" for item in terms.get("limits", []))

    return f"""# Contrat de souscription simulé

**Numéro de contrat :** {contract["contract_id"]}  
**Date de génération :** {contract["generated_at"]}

## Client
- Code Client : {contract["client_code"]}
- Nom : {contract["last_name"]}
- Prénom : {contract["first_name"]}

## Produit souscrit
- Produit : {contract["product_name"]}
- Catégorie : {contract["product_category"]}
- Prix standard : {contract["standard_price"]}
- Prix promotionnel : {contract["promo_price"]}

## Conditions principales
{condition_lines}

## Avantages
{benefit_lines}

## Clause de validation bancaire
{contract["bank_validation_clause"]}

## Terms & Conditions simulées
**Description :** {terms["description"]}

**Éligibilité :**
{terms_eligibility}

**Frais éventuels :** {terms["fees"]}  
**Durée :** {terms["duration"]}  
**Droits de rétractation :** {terms["withdrawal_rights"]}

**Responsabilités client :** {terms["customer_responsibilities"]}

**Responsabilités banque :** {terms["bank_responsibilities"]}

**Limites / points de vigilance :**
{terms_limits}

**Clause conformité :** {terms["compliance_clause"]}

## Signatures simulées
- {contract["client_signature"]}
- {contract["bank_signature"]}
"""
