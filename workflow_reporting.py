from __future__ import annotations

import altair as alt
import pandas as pd


def compute_campaign_kpis(report: pd.DataFrame | None) -> dict[str, int]:
    if report is None or report.empty:
        return {
            "targeted_clients": 0,
            "recommendations": 0,
            "products": 0,
            "pending_validation": 0,
        }
    return {
        "targeted_clients": int(report["Code Client"].nunique()) if "Code Client" in report else 0,
        "recommendations": int(len(report)),
        "products": int(report["Produit recommandé"].nunique()) if "Produit recommandé" in report else 0,
        "pending_validation": int(report["Statut"].astype(str).str.contains("valider", case=False, na=False).sum())
        if "Statut" in report
        else 0,
    }


def build_campaign_charts(report: pd.DataFrame | None) -> dict[str, alt.Chart]:
    if report is None or report.empty:
        return {}

    charts: dict[str, alt.Chart] = {}
    by_product = report.groupby("Produit recommandé", dropna=False).size().reset_index(name="Recommandations")
    charts["products"] = alt.Chart(by_product).mark_bar(cornerRadius=4, color="#0b8ff0").encode(
        x=alt.X("Recommandations:Q", title="Recommandations"),
        y=alt.Y("Produit recommandé:N", title=None, sort="-x"),
        tooltip=["Produit recommandé:N", "Recommandations:Q"],
    )

    if "Cluster" in report.columns:
        by_cluster = report.groupby("Cluster", dropna=False).size().reset_index(name="Clients ciblés")
        charts["clusters"] = alt.Chart(by_cluster).mark_bar(cornerRadius=4, color="#0c2347").encode(
            x=alt.X("Cluster:N", title="Cluster"),
            y=alt.Y("Clients ciblés:Q", title="Clients ciblés"),
            tooltip=["Cluster:N", "Clients ciblés:Q"],
        )

    if "Statut" in report.columns:
        by_status = report.groupby("Statut", dropna=False).size().reset_index(name="Campagnes")
        charts["status"] = alt.Chart(by_status).mark_bar(cornerRadius=4, color="#ff4b4b").encode(
            x=alt.X("Statut:N", title=None),
            y=alt.Y("Campagnes:Q", title="Campagnes"),
            tooltip=["Statut:N", "Campagnes:Q"],
        )

    return charts


def workflow_timeline_rows() -> list[dict[str, object]]:
    return [
        {"Étape": 1, "Action": "Chargement des données", "Statut": "Simulé"},
        {"Étape": 2, "Action": "Analyse des clients", "Statut": "Simulé"},
        {"Étape": 3, "Action": "Génération des recommandations", "Statut": "Simulé"},
        {"Étape": 4, "Action": "Application des promotions", "Statut": "Simulé"},
        {"Étape": 5, "Action": "Génération des messages", "Statut": "Simulé"},
        {"Étape": 6, "Action": "Campagne prête pour validation", "Statut": "À valider"},
    ]
