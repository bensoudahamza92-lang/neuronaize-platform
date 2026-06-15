from __future__ import annotations

from product_catalog import get_product_details
from product_rag import UNAVAILABLE_MESSAGE, ProductRAGIndex, answer_from_catalog


ALLOWED_TOPICS = {
    "avantage",
    "avantages",
    "benefit",
    "benefits",
    "limite",
    "limites",
    "vigilance",
    "eligibilite",
    "éligibilité",
    "eligible",
    "commercial",
    "argument",
    "pertinent",
    "pertinence",
    "pourquoi",
    "why",
    "condition",
    "conditions",
}


def answer_product_question(
    question: str,
    product_name: str,
    score: float,
    cluster_label: str,
    language: str = "fr",
    catalog_product: dict[str, object] | None = None,
    rag_index: ProductRAGIndex | None = None,
) -> str:
    """Return a constrained product-assistant answer from the uploaded catalogue."""

    normalized = question.lower()
    details = get_product_details(product_name, score, cluster_label, catalog_product)

    if catalog_product is not None:
        if rag_index is not None:
            return answer_from_catalog(
                rag_index,
                question,
                product_source_column=str(catalog_product.get("Colonne source bddf2", product_name)),
            )

        if any(token in normalized for token in ["condition", "elig", "élig"]):
            items = details.get("eligibility", [])
        elif any(token in normalized for token in ["avantage", "benefit", "bénéfice"]):
            items = details.get("benefits", [])
        elif any(token in normalized for token in ["limite", "vigilance", "risque", "watch"]):
            items = details.get("limits", [])
        elif any(token in normalized for token in ["argument", "commercial", "vente", "sales"]):
            items = details.get("sales_arguments", [])
        elif any(token in normalized for token in ["description", "quoi", "what", "présente", "presente"]):
            items = [details.get("description", "")]
        else:
            return UNAVAILABLE_MESSAGE

        return "\n".join([str(item) for item in items if str(item).strip()]) or UNAVAILABLE_MESSAGE

    if rag_index is not None:
        return UNAVAILABLE_MESSAGE

    if not any(topic in normalized for topic in ALLOWED_TOPICS):
        if language == "en":
            return (
                "I can only answer questions about this product's benefits, limits, eligibility, "
                "sales arguments, or why it is relevant for this customer."
            )
        return (
            "Je peux répondre uniquement sur les avantages, les limites, les conditions d'éligibilité, "
            "les arguments commerciaux ou la pertinence de ce produit pour ce client."
        )

    if language == "en":
        return (
            f"For {details['name']}, the recommendation score is {score:.1f}%. "
            f"It is relevant because the customer belongs to the segment {cluster_label}. "
            "Key benefits: better targeted advisory, segment-based prioritization, and a clearer sales conversation. "
            "Main watch-outs: validate eligibility, customer suitability, and regulatory constraints before any offer."
        )

    return (
        f"Pour {details['name']}, le score de recommandation est de {score:.1f}%. "
        f"Le produit est pertinent car le client appartient au segment {cluster_label}. "
        "Les principaux avantages sont une proposition mieux ciblée, une priorisation fondée sur les clients similaires "
        "et un discours commercial plus clair. Points de vigilance : vérifier l'éligibilité, l'adéquation au besoin "
        "et les contraintes réglementaires avant toute proposition."
    )


def answer_subscription_question(step: int, client_name: str, product_name: str) -> str:
    """Return a guided demo answer for the subscription assistant."""

    if step <= 1:
        return "Je vérifie d'abord l'identité client : Code Client, nom et prénom."
    if step == 2:
        return f"Identité confirmée pour {client_name}. Je prépare maintenant la demande pour {product_name}."
    if step == 3:
        return "Résumé prêt. Vous pouvez générer le contrat simulé et les Terms & Conditions."
    if step == 4:
        return "Contrat simulé généré. La confirmation finale enregistrera une demande en attente de validation bancaire."
    return "Demande enregistrée. Aucune souscription réelle n'a été finalisée dans cette démo."
