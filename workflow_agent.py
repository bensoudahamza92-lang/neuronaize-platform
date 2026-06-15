from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import cycle

import pandas as pd

from campaign_manager import campaign_offer_label
from notification_simulator import simulate_notification_batch
from product_catalog import catalog_display_name, get_catalog_product, split_catalog_field
from promotion_manager import get_active_promotion, promotion_to_offer_config


@dataclass
class WorkflowConfig:
    workflow_name: str
    execution_frequency: str
    day_of_month: int
    execution_time: str
    workflow_enabled: bool
    recommendation_threshold: float
    max_products_per_client: int
    selected_channels: list[str]
    require_human_validation: bool
    campaign_status: str = "Brouillon"
    excluded_clusters: list[int] | None = None
    expert_weight: float = 0.0


def create_workflow_config(
    workflow_name: str = "Campagne cross-selling NeuronAIze",
    execution_frequency: str = "Chaque mois",
    day_of_month: int = 5,
    execution_time: str = "08:00",
    workflow_enabled: bool = True,
    recommendation_threshold: float = 0.30,
    max_products_per_client: int = 2,
    selected_channels: list[str] | None = None,
    require_human_validation: bool = True,
    campaign_status: str = "Brouillon",
    excluded_clusters: list[int] | None = None,
    expert_weight: float = 0.0,
) -> WorkflowConfig:
    return WorkflowConfig(
        workflow_name=workflow_name,
        execution_frequency=execution_frequency,
        day_of_month=day_of_month,
        execution_time=execution_time,
        workflow_enabled=workflow_enabled,
        recommendation_threshold=recommendation_threshold,
        max_products_per_client=max_products_per_client,
        selected_channels=selected_channels or ["Email"],
        require_human_validation=require_human_validation,
        campaign_status=campaign_status,
        excluded_clusters=excluded_clusters or [],
        expert_weight=expert_weight,
    )


def simulate_workflow(
    config: WorkflowConfig,
    client_count: int,
    product_count: int,
    promotion_count: int = 0,
    rules_loaded: bool = False,
) -> dict[str, object]:
    return {
        "Workflow": config.workflow_name,
        "Fréquence": config.execution_frequency,
        "Jour du mois": config.day_of_month if config.execution_frequency == "Chaque mois" else "-",
        "Heure": config.execution_time,
        "Workflow actif": "Oui" if config.workflow_enabled else "Non",
        "Clients éligibles": client_count,
        "Produits max/client": config.max_products_per_client,
        "Canaux": ", ".join(config.selected_channels),
        "Promotions actives": promotion_count,
        "Règles métier": "Chargées" if rules_loaded else "Non chargées",
        "Validation humaine": "Obligatoire" if config.require_human_validation else "Non obligatoire",
        "Statut": config.campaign_status,
        "Produits détectés": product_count,
    }


def generate_client_message(
    channel: str,
    product_name: str,
    score: float,
    offer_config: dict[str, object],
    catalog_product: dict[str, object] | None = None,
) -> str:
    product_display = catalog_display_name(product_name, catalog_product)
    promo_message = str(offer_config.get("promo_message", "")).strip()
    promo_price = str(offer_config.get("promo_price", "")).strip()

    if channel == "SMS":
        suffix = f" Offre: {promo_price}." if promo_price else ""
        return f"NeuronAIze: {product_display} peut vous intéresser ({score:.0f}%).{suffix}"

    if channel == "Push notification app mobile":
        return f"Découvrez {product_display}: offre personnalisée disponible."

    benefits = split_catalog_field(catalog_product.get("Avantages", "")) if catalog_product else []
    benefit_text = f" Avantage clé : {benefits[0]}." if benefits else ""
    promo_text = f" {promo_message}" if promo_message else ""
    return (
        f"Bonjour, nous avons identifié une opportunité personnalisée autour de {product_display} "
        f"avec un score de pertinence de {score:.0f}%.{benefit_text}{promo_text}"
    )


def generate_recommendation_report(
    recommender,
    catalog: pd.DataFrame | None,
    config: WorkflowConfig,
    offer_config: dict[str, object],
    promotions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Generate a cross-selling campaign report from the recommender system."""

    if recommender is None or recommender.training_data_ is None:
        raise ValueError("Le moteur de recommandation n'est pas entraîné.")

    channels = config.selected_channels or ["Email"]
    channel_cycle = cycle(channels)
    rows = []

    for _, customer in recommender.training_data_.drop(columns=["_cluster"], errors="ignore").iterrows():
        customer_df = customer.to_frame().T
        cluster_id = recommender.predict_cluster(customer_df)
        if cluster_id in (config.excluded_clusters or []):
            continue

        recommendations = recommender.recommend(customer_df, threshold=config.recommendation_threshold)
        if recommendations.empty:
            recommendations = generate_fallback_recommendations(recommender, customer_df, cluster_id)
        if recommendations.empty:
            continue

        for _, recommendation in recommendations.head(config.max_products_per_client).iterrows():
            product_column = recommendation["Produit"]
            score = min(100.0, float(recommendation["Score %"]) * (1 + float(config.expert_weight or 0)))
            channel = next(channel_cycle)
            catalog_product = get_catalog_product(catalog, product_column)
            product_display = catalog_display_name(product_column, catalog_product)
            active_promotion = get_active_promotion(promotions, product_column)
            product_offer_config = promotion_to_offer_config(active_promotion, offer_config)
            message = generate_client_message(channel, product_column, score, product_offer_config, catalog_product)

            rows.append(
                {
                    "Code Client": customer.get(recommender.client_code_column, ""),
                    "Cluster": cluster_id,
                    "Produit recommandé": product_display,
                    "Colonne source bddf2": product_column,
                    "Score de recommandation": score,
                    "Canal proposé": channel,
                    "Message commercial proposé": message,
                    "Offre associée": campaign_offer_label(product_offer_config),
                    "Promotion active": "Oui" if active_promotion else "Non",
                    "Statut": "À valider" if config.require_human_validation else "Brouillon",
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "Code Client",
            "Cluster",
            "Produit recommandé",
            "Colonne source bddf2",
            "Score de recommandation",
            "Canal proposé",
            "Message commercial proposé",
            "Offre associée",
            "Promotion active",
            "Statut",
        ],
    )


def generate_fallback_recommendations(recommender, customer_df: pd.DataFrame, cluster_id: int) -> pd.DataFrame:
    """Return best non-owned cluster products even when the threshold is too restrictive.

    This keeps the campaign report usable for demos while still excluding products
    already held by the customer.
    """

    cluster_rows = recommender.training_data_[recommender.training_data_["_cluster"] == cluster_id]
    if cluster_rows.empty:
        return pd.DataFrame(columns=["Produit", "Score %", "Source", "Cluster", "Clients similaires"])

    customer = customer_df.iloc[0]
    rows = []
    for product in recommender.product_columns:
        value = customer.get(product, 0)
        try:
            owns_product = float(value) > 0
        except (TypeError, ValueError):
            owns_product = str(value).strip().lower() in {"oui", "yes", "true", "vrai", "1"}
        if owns_product:
            continue

        product_rate = cluster_rows[product].apply(product_ownership_flag).mean()
        if product_rate <= 0:
            continue

        rows.append(
            {
                "Produit": product,
                "Score %": round(float(product_rate) * 100, 1),
                "Source": f"Cluster {cluster_id} ({len(cluster_rows)} clients similaires)",
                "Cluster": cluster_id,
                "Clients similaires": len(cluster_rows),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["Produit", "Score %", "Source", "Cluster", "Clients similaires"])
    return pd.DataFrame(rows).sort_values("Score %", ascending=False).reset_index(drop=True)


def product_ownership_flag(value: object) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"oui", "yes", "true", "vrai"}:
            return 1
        try:
            return int(float(normalized) > 0)
        except ValueError:
            return 0
    return int(float(value) > 0)


def validate_campaign(report: pd.DataFrame, require_human_validation: bool = True) -> pd.DataFrame:
    if report is None or report.empty:
        return pd.DataFrame()

    validated = report.copy()
    if require_human_validation:
        validated["Statut"] = "Validé"
    return validated


def simulate_notifications(
    report: pd.DataFrame,
    require_human_validation: bool = True,
    campaign_validated: bool = False,
) -> pd.DataFrame:
    return simulate_notification_batch(report, require_human_validation, campaign_validated)
