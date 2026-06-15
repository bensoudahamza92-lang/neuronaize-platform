from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from uuid import uuid4

import altair as alt
import pandas as pd
import streamlit as st

from chatbot import answer_product_question
from campaign_manager import report_to_excel_bytes
from compliance_checker import check_workflow_compliance, violations_to_dataframe
from contract_generator import generate_contract, generate_terms_and_conditions, format_contract_as_markdown
from product_catalog import (
    catalog_display_name,
    clean_product_name,
    get_catalog_offer_fields,
    get_catalog_product,
    get_product_details,
    get_product_icon,
    prepare_catalog,
    split_catalog_field,
    validate_catalog,
)
from product_rag import build_product_rag_index
from promotion_manager import (
    export_promotions,
    load_promotions,
    prepare_promotions,
    save_promotions,
    upsert_promotion,
)
from recommender import (
    BankingRecommender,
    detect_product_columns,
    find_client_code_column,
    normalize_client_code,
)
from workflow_reporting import build_campaign_charts, compute_campaign_kpis, workflow_timeline_rows
from workflow_schemas import WorkflowJSONDefinition, WorkflowJSONEdge, WorkflowJSONNode
from subscription_agent import (
    STATUS_PENDING,
    create_subscription_request,
    get_subscription_status_badge,
    initialize_subscription_session,
    save_subscription_to_excel,
    validate_client_identity,
)
from subscription_reporting import (
    build_subscription_charts,
    compute_subscription_kpis,
    export_subscriptions,
    load_subscriptions,
)
from workflow_agent import (
    create_workflow_config,
    generate_recommendation_report,
    simulate_notifications,
    simulate_workflow,
    validate_campaign,
)
from ui_components import (
    badge,
    chat_message,
    client_field_grid,
    detail_card,
    inject_premium_css,
    metric_card,
    product_card,
    render_header,
    section_end,
    section_start,
    security_notice,
    status_badge,
    timeline,
)


st.set_page_config(
    page_title="NeuronAIze - Recommandations bancaires",
    layout="wide",
    initial_sidebar_state="expanded",
)


LOGO_PATH = Path(__file__).parent / "assets" / "neuronaize-logo-baseline.png"
AUTO_CLUSTER_MIN = 3
AUTO_CLUSTER_SEARCH_LIMIT = 10


TRANSLATIONS = {
    "fr": {
        "fr": "Français",
        "en": "Anglais",
        "title": "NeuronAIze - Moteur intelligent de recommandations bancaires",
        "subtitle": "Démo bancaire premium : segmentation client, analyse de similarité et recommandations actionnables.",
        "data": "Données",
        "screen": "Écran",
        "screen_engine": "Moteur de recommandation",
        "screen_catalog": "Catalogue Produit",
        "screen_workflow": "Workflow Agent IA",
        "screen_agent_console": "Console Agent IA",
        "screen_subscription": "Souscription assistée",
        "screen_reporting": "Reporting Souscriptions",
        "agent_console_title": "Console Agent IA",
        "agent_console_caption": "Supervision des workflows, validations humaines et propositions générées par l’agent.",
        "hitl_mode": "Mode Human In The Loop",
        "hitl_sync": "Synchrone",
        "hitl_exception": "Par exception",
        "hitl_copilot": "Copilote",
        "executed_workflows": "Workflows exécutés",
        "execution_logs": "Logs d’exécution",
        "pending_validation_steps": "Étapes en attente de validation",
        "ai_generated_proposals": "Propositions générées par l’IA",
        "approve": "Approuver",
        "reject": "Rejeter",
        "modify_proposal": "Modifier proposition",
        "proposal_modified": "Proposition modifiée et sauvegardée en session.",
        "proposal_approved": "Proposition approuvée. Aucun envoi réel n’est déclenché.",
        "proposal_rejected": "Proposition rejetée.",
        "no_agent_activity": "Aucune activité agent disponible. Lancez une simulation ou générez un rapport dans Workflow Agent IA.",
        "subscription_title": "Souscription assistée par Agent IA",
        "subscription_caption": "Transformer une recommandation en intention de souscription mesurable, avec contrat simulé et validation bancaire finale.",
        "subscription_button": "Souscrire à ce produit",
        "subscription_no_context": "Sélectionnez d’abord un produit recommandé depuis le moteur de recommandation.",
        "subscription_security_title": "Simulation réglementée",
        "subscription_security_text": "Ce workflow est une simulation. Toute souscription réelle doit être validée par les processus réglementaires et opérationnels de la banque.",
        "subscription_identity": "Identité client",
        "subscription_product": "Produit sélectionné",
        "subscription_summary": "Résumé de la demande",
        "generate_contract": "Générer contrat simulé",
        "confirm_subscription": "Confirmer la demande de souscription",
        "subscription_saved": "Demande enregistrée avec le statut En attente de validation.",
        "subscription_status": "Statut souscription",
        "contract_block": "Contrat simulé",
        "terms_block": "Terms & Conditions simulées",
        "client_last_name": "Nom",
        "client_first_name": "Prénom",
        "notification_channel": "Canal préféré",
        "reporting_title": "Reporting Souscriptions",
        "reporting_caption": "Mesurer les intentions et demandes de souscription générées par les recommandations NeuronAIze.",
        "no_subscriptions": "Aucune souscription enregistrée pour le moment.",
        "total_subscriptions": "Souscriptions",
        "pending_subscriptions": "En attente",
        "validated_subscriptions": "Validées",
        "potential_revenue": "CA potentiel",
        "by_product": "Par produit",
        "by_status": "Par statut",
        "by_date": "Évolution par date",
        "by_category": "Par catégorie",
        "export_subscriptions": "Exporter les souscriptions",
        "workflow_agent_title": "Workflow Agent IA - Automatisation du cross-selling",
        "workflow_agent_caption": "L’Agent IA prépare les campagnes. La banque garde toujours la validation finale avant activation.",
        "planning": "Planification",
        "data_sources": "Sources de données",
        "recommendation_rules": "Règles de recommandation",
        "offers": "Offres et promotions",
        "channels": "Canaux de notification",
        "simulation": "Simulation",
        "generated_report": "Rapport généré",
        "campaign_validation": "Validation campagne",
        "workflow_name": "Nom du workflow",
        "frequency": "Fréquence d’exécution",
        "daily": "Chaque jour",
        "weekly": "Chaque semaine",
        "monthly": "Chaque mois",
        "day_of_month": "Jour du mois",
        "execution_time": "Heure d’exécution",
        "workflow_enabled": "Workflow actif",
        "client_source": "Base clients Excel",
        "catalog_source": "Catalogue produit Excel",
        "promotion_source": "Fichier des offres promotionnelles",
        "rules_source": "Fichier des règles métier",
        "max_products_client": "Nombre maximum de produits recommandés par client",
        "exclude_owned": "Exclure les produits déjà détenus",
        "exclude_clusters": "Exclure certains clusters",
        "expert_weight": "Pondération recommandations expertes",
        "human_validation": "Validation humaine obligatoire",
        "standard_price": "Prix standard du produit",
        "promo_price": "Prix promotionnel",
        "offer_start": "Date de début de l’offre",
        "offer_end": "Date de fin de l’offre",
        "promo_message": "Message promotionnel",
        "product_campaign_active": "Campagne produit active",
        "product_source_column": "Colonne source produit",
        "save_promotion": "Sauvegarder la promotion",
        "promotions_saved": "Promotion sauvegardée localement.",
        "active_promotions": "Promotions actives",
        "advisor_call": "Appel conseiller",
        "simulate_workflow": "Simuler le workflow",
        "generate_report": "Générer le rapport",
        "validate_campaign": "Valider la campagne",
        "export_excel": "Exporter le rapport Excel",
        "email": "Email",
        "sms": "SMS",
        "push": "Push notification app mobile",
        "workflow_no_client_file": "Chargez une base clients Excel pour simuler le workflow.",
        "workflow_catalog_missing": "Catalogue produit non chargé : le rapport sera généré avec les noms techniques des produits.",
        "workflow_no_recommendation": "Aucune recommandation disponible avec les règles configurées.",
        "workflow_validated": "Campagne validée. L’envoi reste simulé pour la démo.",
        "simulated_send": "Envoi simulé",
        "workflow_timeline": "Timeline d’exécution simulée",
        "targeted_clients": "Clients ciblés",
        "generated_recommendations": "Recommandations générées",
        "top_products": "Produits les plus proposés",
        "targeted_segments": "Segmentation ciblée",
        "pending_campaigns": "Campagnes en attente",
        "rules_help_title": "Comprendre les règles",
        "rules_help_score": "Seuil 0 à 1",
        "rules_help_score_text": "0.30 signifie 30 %. Un produit est recommandé si au moins 30 % des clients similaires le détiennent.",
        "rules_help_max": "Maximum par client",
        "rules_help_max_text": "Limite le nombre de produits proposés pour éviter une campagne trop chargée.",
        "rules_help_owned": "Produits déjà détenus",
        "rules_help_owned_text": "Un produit avec valeur 1 est déjà détenu. Un produit avec valeur 0 peut être proposé si le score est suffisant.",
        "rules_help_validation": "Validation humaine",
        "rules_help_validation_text": "L’agent prépare la campagne, mais la banque doit valider avant toute activation. Aucun message réel n’est envoyé.",
        "rules_help_clusters": "Exclusion de clusters",
        "rules_help_clusters_text": "Permet d’écarter certains segments clients de la campagne, par exemple un cluster non prioritaire.",
        "draft": "Brouillon",
        "to_validate": "À valider",
        "validated": "Validé",
        "catalog_title": "Catalogue Produit",
        "catalog_caption": "Uploader, valider et indexer le catalogue produit utilisé par les recommandations et l’assistant produit basé sur le catalogue.",
        "catalog_upload": "Charger le fichier Excel catalogue produit",
        "catalog_sidebar_upload": "Catalogue produit Excel",
        "catalog_loaded": "Catalogue chargé",
        "catalog_load_error": "Catalogue produit invalide",
        "catalog_product_not_found": "Ce produit recommandé n’a pas de fiche correspondante dans le catalogue chargé.",
        "catalog_chat_strict": "Mode C2 actif : le chatbot répond uniquement à partir du catalogue produit chargé.",
        "catalog_preview": "Aperçu du catalogue",
        "catalog_valid": "Catalogue valide et indexé localement.",
        "catalog_missing": "Colonnes obligatoires manquantes",
        "catalog_rows": "Produits catalogue",
        "catalog_index": "Catalogue produit indexé",
        "catalog_helper": "Le moteur fonctionne sans API externe : les réponses sont générées à partir des champs du catalogue uploadé.",
        "catalog_not_loaded": "Aucun catalogue produit chargé. Les recommandations utilisent les contenus génériques.",
        "category": "Catégorie",
        "eligibility": "Conditions d’éligibilité",
        "upload": "Charger le fichier Excel client",
        "settings": "Paramètres",
        "threshold": "Seuil de recommandation",
        "threshold_help": "Produit recommandé si son taux de détention dans le cluster dépasse ce seuil.",
        "min_clusters": "Minimum clusters",
        "min_clusters_help": "Minimum métier retenu pour obtenir une segmentation bancaire suffisamment riche.",
        "max_clusters": "Maximum clusters",
        "max_clusters_help": "Le moteur teste les valeurs de k jusqu’à ce maximum pour détecter le coude d’inertie.",
        "inertia_title": "Diagnostic du nombre de clusters",
        "inertia_caption": "Le nombre de clusters est sélectionné automatiquement à partir du coude de la courbe d’inertie.",
        "selected_k": "Nombre de clusters retenu",
        "selection_method": "Méthode utilisée",
        "inertia_curve": "Courbe d’inertie KMedoids",
        "workflow": "Parcours",
        "step_1": "1. Clustering",
        "step_2": "2. Fiche client",
        "step_3": "3. Recommandations",
        "step_4": "4. Détail produit",
        "step_5": "5. Chatbot produit",
        "step_6": "6. Souscription",
        "step_7": "7. Mesure",
        "no_file": "Chargez un fichier Excel pour démarrer l'analyse NeuronAIze.",
        "read_error": "Impossible de lire le fichier Excel",
        "empty_file": "Le fichier chargé ne contient aucune donnée.",
        "missing_products": 'Aucune colonne produit détectée. Les colonnes produits doivent commencer par "Produit -".',
        "analysis_error": "Erreur pendant le clustering",
        "analysis_spinner": "Analyse des profils clients et entraînement du clustering...",
        "cluster_title": "Résultat du clustering",
        "cluster_caption": "Le moteur segmente les clients sur les caractéristiques client uniquement. Les produits servent ensuite à calculer les opportunités.",
        "clients": "Clients analysés",
        "clusters": "Clusters retenus",
        "products": "Produits détectés",
        "code_column": "Code Client",
        "cluster_size": "Taille des clusters",
        "summary": "Résumé des clusters",
        "dominant_profile": "Profil dominant",
        "enter_code": "Entrer le Code Client",
        "select_code": "Choisir le Code Client",
        "validate": "Valider",
        "client_error": "Recherche client impossible",
        "client_title": "Fiche client",
        "client_caption": "Vue conseiller : identité, situation et indicateurs comportementaux.",
        "owned_products": "Produits déjà souscrits",
        "no_owned_products": "Aucun produit souscrit détecté pour ce client.",
        "analyze": "Analyser avec NeuronAIze",
        "recommendation_error": "Impossible de générer les recommandations",
        "recommendations_title": "Recommandations NeuronAIze",
        "recommendations_caption": "Produits non détenus par le client et fréquents chez les clients similaires.",
        "no_recommendations": "Aucune recommandation disponible au seuil sélectionné.",
        "similar_customers": "clients similaires",
        "details": "Voir détails",
        "chart_title": "Scores de recommandation",
        "product_detail": "Détail produit",
        "why": "Pourquoi ce produit est adapté",
        "benefits": "Avantages",
        "limits": "Limites / points de vigilance",
        "sales": "Arguments commerciaux",
        "chatbot": "Discuter avec le chatbot produit",
        "chat_placeholder": "Posez une question sur les avantages, limites, éligibilité ou arguments commerciaux...",
        "send": "Envoyer",
        "chat_intro": "Le chatbot répond uniquement sur le produit sélectionné et son adéquation au client.",
        "preview": "Aperçu contrôlé des données",
        "profile_label": "Libellé automatique",
    },
    "en": {
        "fr": "French",
        "en": "English",
        "title": "NeuronAIze - Intelligent Banking Recommendation Engine",
        "subtitle": "Premium banking demo: customer segmentation, similarity analysis, and actionable recommendations.",
        "data": "Data",
        "screen": "Screen",
        "screen_engine": "Recommendation engine",
        "screen_catalog": "Product Catalogue",
        "screen_workflow": "AI Agent Workflow",
        "screen_agent_console": "AI Agent Console",
        "screen_subscription": "Assisted subscription",
        "screen_reporting": "Subscription Reporting",
        "agent_console_title": "AI Agent Console",
        "agent_console_caption": "Monitor workflows, human validations, and proposals generated by the agent.",
        "hitl_mode": "Human In The Loop mode",
        "hitl_sync": "Synchronous",
        "hitl_exception": "By exception",
        "hitl_copilot": "Copilot",
        "executed_workflows": "Executed workflows",
        "execution_logs": "Execution logs",
        "pending_validation_steps": "Steps pending validation",
        "ai_generated_proposals": "AI-generated proposals",
        "approve": "Approve",
        "reject": "Reject",
        "modify_proposal": "Modify proposal",
        "proposal_modified": "Proposal modified and saved in session.",
        "proposal_approved": "Proposal approved. No real sending is triggered.",
        "proposal_rejected": "Proposal rejected.",
        "no_agent_activity": "No agent activity available. Run a simulation or generate a report in AI Agent Workflow.",
        "subscription_title": "AI Agent Assisted Subscription",
        "subscription_caption": "Turn a recommendation into a measurable subscription intent, with a simulated contract and final bank validation.",
        "subscription_button": "Subscribe to this product",
        "subscription_no_context": "Select a recommended product from the recommendation engine first.",
        "subscription_security_title": "Regulated simulation",
        "subscription_security_text": "This workflow is a simulation. Any real subscription must be validated through the bank's regulatory and operational processes.",
        "subscription_identity": "Customer identity",
        "subscription_product": "Selected product",
        "subscription_summary": "Request summary",
        "generate_contract": "Generate simulated contract",
        "confirm_subscription": "Confirm subscription request",
        "subscription_saved": "Request saved with Pending bank validation status.",
        "subscription_status": "Subscription status",
        "contract_block": "Simulated contract",
        "terms_block": "Simulated Terms & Conditions",
        "client_last_name": "Last name",
        "client_first_name": "First name",
        "notification_channel": "Preferred channel",
        "reporting_title": "Subscription Reporting",
        "reporting_caption": "Measure subscription intents and requests generated by NeuronAIze recommendations.",
        "no_subscriptions": "No subscription request has been saved yet.",
        "total_subscriptions": "Subscriptions",
        "pending_subscriptions": "Pending",
        "validated_subscriptions": "Validated",
        "potential_revenue": "Potential revenue",
        "by_product": "By product",
        "by_status": "By status",
        "by_date": "Trend by date",
        "by_category": "By category",
        "export_subscriptions": "Export subscriptions",
        "workflow_agent_title": "AI Agent Workflow - Cross-selling automation",
        "workflow_agent_caption": "The AI Agent prepares campaigns. The bank always keeps final validation before activation.",
        "planning": "Planning",
        "data_sources": "Data sources",
        "recommendation_rules": "Recommendation rules",
        "offers": "Offers and promotions",
        "channels": "Notification channels",
        "simulation": "Simulation",
        "generated_report": "Generated report",
        "campaign_validation": "Campaign validation",
        "workflow_name": "Workflow name",
        "frequency": "Execution frequency",
        "daily": "Every day",
        "weekly": "Every week",
        "monthly": "Every month",
        "day_of_month": "Day of month",
        "execution_time": "Execution time",
        "workflow_enabled": "Workflow enabled",
        "client_source": "Customer Excel base",
        "catalog_source": "Product catalogue Excel",
        "promotion_source": "Promotional offers file",
        "rules_source": "Business rules file",
        "max_products_client": "Maximum recommended products per customer",
        "exclude_owned": "Exclude already owned products",
        "exclude_clusters": "Exclude segments or clusters",
        "expert_weight": "Expert recommendation weighting",
        "human_validation": "Mandatory human validation",
        "standard_price": "Standard product price",
        "promo_price": "Promotional price",
        "offer_start": "Offer start date",
        "offer_end": "Offer end date",
        "promo_message": "Promotional message",
        "product_campaign_active": "Product campaign active",
        "product_source_column": "Product source column",
        "save_promotion": "Save promotion",
        "promotions_saved": "Promotion saved locally.",
        "active_promotions": "Active promotions",
        "advisor_call": "Advisor call",
        "simulate_workflow": "Simulate workflow",
        "generate_report": "Generate report",
        "validate_campaign": "Validate campaign",
        "export_excel": "Export Excel report",
        "email": "Email",
        "sms": "SMS",
        "push": "Mobile app push notification",
        "workflow_no_client_file": "Upload a customer Excel base to simulate the workflow.",
        "workflow_catalog_missing": "Product catalogue not loaded: the report will use technical product names.",
        "workflow_no_recommendation": "No recommendation available with the configured rules.",
        "workflow_validated": "Campaign validated. Sending remains simulated for the demo.",
        "simulated_send": "Simulated sending",
        "workflow_timeline": "Simulated execution timeline",
        "targeted_clients": "Targeted clients",
        "generated_recommendations": "Generated recommendations",
        "top_products": "Most proposed products",
        "targeted_segments": "Targeted segmentation",
        "pending_campaigns": "Pending campaigns",
        "rules_help_title": "Understanding the rules",
        "rules_help_score": "Threshold 0 to 1",
        "rules_help_score_text": "0.30 means 30%. A product is recommended when at least 30% of similar customers own it.",
        "rules_help_max": "Maximum per customer",
        "rules_help_max_text": "Limits the number of products suggested to avoid an overloaded campaign.",
        "rules_help_owned": "Already owned products",
        "rules_help_owned_text": "A product with value 1 is already owned. A product with value 0 can be proposed if the score is high enough.",
        "rules_help_validation": "Human validation",
        "rules_help_validation_text": "The agent prepares the campaign, but the bank must validate before activation. No real message is sent.",
        "rules_help_clusters": "Cluster exclusion",
        "rules_help_clusters_text": "Lets the bank exclude some customer segments from the campaign, for example a non-priority cluster.",
        "draft": "Draft",
        "to_validate": "To validate",
        "validated": "Validated",
        "catalog_title": "Product Catalogue",
        "catalog_caption": "Upload, validate, and index the product catalogue used by recommendations and the catalogue-based product assistant.",
        "catalog_upload": "Upload the product catalogue Excel file",
        "catalog_sidebar_upload": "Product catalogue Excel",
        "catalog_loaded": "Catalogue loaded",
        "catalog_load_error": "Invalid product catalogue",
        "catalog_product_not_found": "This recommended product has no matching record in the loaded catalogue.",
        "catalog_chat_strict": "C2 mode active: the chatbot answers only from the loaded product catalogue.",
        "catalog_preview": "Catalogue preview",
        "catalog_valid": "Catalogue is valid and locally indexed.",
        "catalog_missing": "Missing mandatory columns",
        "catalog_rows": "Catalogue products",
        "catalog_index": "Indexed product catalogue",
        "catalog_helper": "The engine works without an external API: answers are generated from the uploaded catalogue fields.",
        "catalog_not_loaded": "No product catalogue loaded. Recommendations use generic content.",
        "category": "Category",
        "eligibility": "Eligibility conditions",
        "upload": "Upload the customer Excel file",
        "settings": "Settings",
        "threshold": "Recommendation threshold",
        "threshold_help": "A product is recommended when its ownership rate in the cluster is above this threshold.",
        "min_clusters": "Minimum clusters",
        "min_clusters_help": "Business minimum used to keep the banking segmentation sufficiently rich.",
        "max_clusters": "Maximum clusters",
        "max_clusters_help": "The engine tests k values up to this maximum to detect the inertia elbow.",
        "inertia_title": "Cluster count diagnostic",
        "inertia_caption": "The number of clusters is selected automatically from the elbow of the inertia curve.",
        "selected_k": "Selected number of clusters",
        "selection_method": "Selection method",
        "inertia_curve": "KMedoids inertia curve",
        "workflow": "Workflow",
        "step_1": "1. Clustering",
        "step_2": "2. Customer profile",
        "step_3": "3. Recommendations",
        "step_4": "4. Product detail",
        "step_5": "5. Product chatbot",
        "step_6": "6. Subscription",
        "step_7": "7. Measurement",
        "no_file": "Upload an Excel file to start the NeuronAIze analysis.",
        "read_error": "Unable to read the Excel file",
        "empty_file": "The uploaded file does not contain any data.",
        "missing_products": 'No product column detected. Product columns must start with "Produit -".',
        "analysis_error": "Clustering error",
        "analysis_spinner": "Analyzing customer profiles and training clustering...",
        "cluster_title": "Clustering result",
        "cluster_caption": "The engine segments customers using customer features only. Product ownership is used afterward for opportunities.",
        "clients": "Analyzed clients",
        "clusters": "Selected clusters",
        "products": "Detected products",
        "code_column": "Customer code",
        "cluster_size": "Cluster size",
        "summary": "Cluster summary",
        "dominant_profile": "Dominant profile",
        "enter_code": "Enter Customer Code",
        "select_code": "Choose Customer Code",
        "validate": "Validate",
        "client_error": "Customer lookup failed",
        "client_title": "Customer profile",
        "client_caption": "Advisor view: identity, situation, and behavioral indicators.",
        "owned_products": "Already subscribed products",
        "no_owned_products": "No subscribed product detected for this customer.",
        "analyze": "Analyze with NeuronAIze",
        "recommendation_error": "Unable to generate recommendations",
        "recommendations_title": "NeuronAIze recommendations",
        "recommendations_caption": "Products not owned by the customer and common among similar customers.",
        "no_recommendations": "No recommendation available at the selected threshold.",
        "similar_customers": "similar customers",
        "details": "View details",
        "chart_title": "Recommendation scores",
        "product_detail": "Product detail",
        "why": "Why this product fits",
        "benefits": "Benefits",
        "limits": "Limits / watch-outs",
        "sales": "Sales arguments",
        "chatbot": "Discuss with the product chatbot",
        "chat_placeholder": "Ask about benefits, limits, eligibility, or sales arguments...",
        "send": "Send",
        "chat_intro": "The chatbot only answers about the selected product and its fit for this customer.",
        "preview": "Controlled data preview",
        "profile_label": "Automatic label",
    },
}


def tr(key: str) -> str:
    return TRANSLATIONS[st.session_state.get("language", "fr")][key]


def load_excel(uploaded_file) -> pd.DataFrame:
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    return pd.read_excel(uploaded_file, engine="openpyxl")


def load_catalog(uploaded_file) -> pd.DataFrame:
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    return pd.read_excel(uploaded_file, engine="openpyxl")


def register_uploaded_catalog(uploaded_file, source: str = "sidebar") -> bool:
    """Validate, prepare, and index an uploaded product catalogue."""

    if uploaded_file is None:
        return False

    signature = (source, getattr(uploaded_file, "name", "uploaded"), getattr(uploaded_file, "size", None))
    if st.session_state.get("product_catalog_signature") == signature:
        return True

    try:
        raw_catalog = load_catalog(uploaded_file)
    except Exception as exc:
        st.error(f"{tr('read_error')} : {exc}")
        return False

    missing = validate_catalog(raw_catalog)
    if missing:
        st.error(f"{tr('catalog_load_error')} : {', '.join(missing)}")
        return False

    catalog = prepare_catalog(raw_catalog)
    if catalog.empty:
        st.error(tr("empty_file"))
        return False

    st.session_state["product_catalog"] = catalog
    st.session_state["product_catalog_signature"] = signature
    try:
        st.session_state["product_rag_index"] = build_product_rag_index(catalog)
    except Exception as exc:
        st.session_state["product_rag_index"] = None
        st.warning(f"{tr('catalog_index')} : {exc}")

    for key in ["selected_product", "chat_messages"]:
        st.session_state.pop(key, None)
    return True


def translate_cluster_label(label: str) -> str:
    replacements = {
        "Jeunes": "Young customers",
        "Actifs établis": "Established active customers",
        "Seniors": "Senior customers",
        "revenus élevés": "high income",
        "revenus moyens": "middle income",
        "revenus modestes": "modest income",
        "appétence": "interest in",
        "Segment client": "Customer segment",
    }
    translated = str(label)
    for french, english in replacements.items():
        translated = translated.replace(french, english)
    return translated


def display_cluster_summary(summary: pd.DataFrame) -> pd.DataFrame:
    display = summary.copy()
    if st.session_state["language"] == "en" and "Libellé automatique" in display.columns:
        display["Libellé automatique"] = display["Libellé automatique"].map(translate_cluster_label)
    return display


def preferred_client_fields(customer: pd.Series, feature_columns: list[str], code_column: str) -> list[tuple[str, object]]:
    priority_tokens = [
        "âge",
        "age",
        "situation",
        "revenu",
        "statut",
        "marital",
        "propriétaire",
        "proprietaire",
        "enfant",
        "mouvement",
        "carte",
        "digital",
    ]
    fields: list[tuple[str, object]] = [(code_column, customer.get(code_column, "-"))]
    used = {code_column}

    for token in priority_tokens:
        for column in feature_columns:
            if column in used:
                continue
            if token in str(column).lower():
                fields.append((str(column), customer.get(column, "-")))
                used.add(column)
                break

    for column in feature_columns:
        if len(fields) >= 12:
            break
        if column not in used:
            fields.append((str(column), customer.get(column, "-")))
            used.add(column)

    return fields


def owned_products(customer: pd.Series, product_columns: list[str]) -> list[str]:
    products = []
    for column in product_columns:
        value = customer.get(column, 0)
        try:
            is_owned = float(value) > 0
        except (TypeError, ValueError):
            is_owned = str(value).strip().lower() in {"oui", "yes", "true", "vrai", "1"}
        if is_owned:
            products.append(column)
    return products


def first_matching_field(row: pd.Series, candidates: list[str]) -> str:
    normalized = {str(column).strip().lower(): column for column in row.index}
    for candidate in candidates:
        column = normalized.get(candidate.lower())
        if column is not None and pd.notna(row.get(column)):
            return str(row.get(column)).strip()
    return ""


def build_subscription_context(
    customer_row: pd.Series,
    recommender: BankingRecommender,
    product_column: str,
    score: float,
    cluster_label: str,
    catalog_product: dict[str, object] | None,
) -> dict[str, object]:
    details = get_product_details(product_column, score, cluster_label, catalog_product)
    offer_fields = get_catalog_offer_fields(catalog_product)
    client_payload = {
        "code_client": customer_row.get(recommender.client_code_column, ""),
        "nom": first_matching_field(customer_row, ["Nom", "Last name", "NOM", "Nom client"]),
        "prenom": first_matching_field(customer_row, ["Prénom", "Prenom", "First name", "PRENOM", "Prénom client"]),
    }
    product_payload = {
        "source_column": product_column,
        "name": details["name"],
        "category": details.get("category", ""),
        "description": details.get("description", ""),
        "eligibility": details.get("eligibility", []),
        "benefits": details.get("benefits", []),
        "limits": details.get("limits", []),
        "sales_arguments": details.get("sales_arguments", []),
        **offer_fields,
    }
    return {
        "client": client_payload,
        "product": product_payload,
        "score": score,
        "cluster_label": cluster_label,
    }


def recommendation_chart(recommendations: pd.DataFrame) -> None:
    chart_data = recommendations.copy()
    chart_data["Produit court"] = chart_data["Produit"].map(clean_product_name)
    chart = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadius=4, color="#0b8ff0")
        .encode(
            x=alt.X("Score %:Q", title="Score %", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Produit court:N", title=None, sort="-x"),
            tooltip=["Produit court:N", "Score %:Q", "Source:N"],
        )
        .properties(height=max(180, len(chart_data) * 42))
    )
    st.altair_chart(chart, use_container_width=True)


def inertia_chart(diagnostics: pd.DataFrame, selected_k: int) -> None:
    if diagnostics is None or diagnostics.empty:
        return

    chart_data = diagnostics.copy()
    chart_data["k"] = chart_data["k"].astype(int)
    selected = pd.DataFrame({"k": [int(selected_k)]})

    line = (
        alt.Chart(chart_data)
        .mark_line(point=True, color="#0b8ff0")
        .encode(
            x=alt.X("k:O", title="k"),
            y=alt.Y("inertia:Q", title="Inertie"),
            tooltip=["k:O", alt.Tooltip("inertia:Q", format=",.2f")],
        )
    )
    rule = (
        alt.Chart(selected)
        .mark_rule(color="#ff4b4b", strokeWidth=2)
        .encode(x=alt.X("k:O"))
    )
    st.altair_chart((line + rule).properties(height=280), use_container_width=True)


def help_card(title: str, text: str) -> None:
    st.markdown(
        (
            '<div class="help-card">'
            f'<div class="help-card-title">{title}</div>'
            f'<div class="help-card-text">{text}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def log_agent_console_event(action: str, status: str, details: str = "") -> None:
    events = st.session_state.setdefault("agent_console_events", [])
    events.append(
        {
            "ID": f"evt-{uuid4().hex[:8]}",
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Workflow": st.session_state.get("active_workflow_name", "Campagne cross-selling NeuronAIze"),
            "Action": action,
            "Statut": status,
            "Détails": details,
        }
    )


def get_agent_console_events() -> pd.DataFrame:
    events = st.session_state.get("agent_console_events", [])
    if not events:
        return pd.DataFrame(columns=["ID", "Date", "Workflow", "Action", "Statut", "Détails"])
    return pd.DataFrame(events)


def build_console_logs() -> pd.DataFrame:
    logs = []
    events = get_agent_console_events()
    if not events.empty:
        logs.append(events.rename(columns={"Action": "Étape"}))

    timeline = st.session_state.get("workflow_timeline")
    if timeline is not None and not timeline.empty:
        timeline_logs = timeline.copy()
        timeline_logs["ID"] = [f"tl-{idx + 1}" for idx in range(len(timeline_logs))]
        timeline_logs["Date"] = "-"
        timeline_logs["Workflow"] = st.session_state.get("active_workflow_name", "Workflow Agent IA")
        timeline_logs["Détails"] = timeline_logs.get("Action", "")
        timeline_logs = timeline_logs.rename(columns={"Action": "Étape"})
        logs.append(timeline_logs[["ID", "Date", "Workflow", "Étape", "Statut", "Détails"]])

    if not logs:
        return pd.DataFrame(columns=["ID", "Date", "Workflow", "Étape", "Statut", "Détails"])
    combined = pd.concat(logs, ignore_index=True, sort=False)
    return combined[[column for column in ["ID", "Date", "Workflow", "Étape", "Statut", "Détails"] if column in combined]]


def render_catalog_page() -> None:
    section_start(tr("catalog_title"), tr("catalog_caption"))
    catalog_file = st.file_uploader(tr("catalog_upload"), type=["xlsx", "xls"], key="catalog_upload")

    if catalog_file is None:
        st.info(tr("catalog_helper"))
        catalog = st.session_state.get("product_catalog")
        if catalog is not None:
            st.success(tr("catalog_valid"))
            st.dataframe(catalog.head(20), use_container_width=True, hide_index=True)
        section_end()
        return

    try:
        raw_catalog = load_catalog(catalog_file)
    except Exception as exc:
        st.error(f"{tr('read_error')} : {exc}")
        section_end()
        return

    missing = validate_catalog(raw_catalog)
    if missing:
        st.error(f"{tr('catalog_missing')} : {', '.join(missing)}")
        st.dataframe(raw_catalog.head(20), use_container_width=True, hide_index=True)
        section_end()
        return

    catalog = prepare_catalog(raw_catalog)
    if catalog.empty:
        st.error(tr("empty_file"))
        section_end()
        return

    st.session_state["product_catalog"] = catalog
    try:
        st.session_state["product_rag_index"] = build_product_rag_index(catalog)
    except Exception as exc:
        st.session_state["product_rag_index"] = None
        st.warning(f"{tr('catalog_index')} : {exc}")

    metric_cols = st.columns(3)
    with metric_cols[0]:
        metric_card(tr("catalog_rows"), len(catalog), catalog_file.name)
    with metric_cols[1]:
        metric_card(tr("catalog_index"), "OK", "FAISS / local fallback")
    with metric_cols[2]:
        metric_card(tr("products"), catalog["Catégorie"].nunique(), tr("category"))

    st.success(tr("catalog_valid"))
    st.markdown(f"**{tr('catalog_preview')}**")
    st.dataframe(catalog.head(30), use_container_width=True, hide_index=True)

    if not catalog.empty:
        product_cols = st.columns(min(3, len(catalog)))
        for idx, (_, row) in enumerate(catalog.head(6).iterrows()):
            with product_cols[idx % len(product_cols)]:
                product_card(
                    str(row["Nom produit"]),
                    get_product_icon(str(row["Nom produit"]), str(row["Catégorie"])),
                    category=str(row["Catégorie"]),
                    description=str(row["Description"])[:180],
                    benefits=split_catalog_field(row["Avantages"]),
                    eligibility=split_catalog_field(row["Conditions d’éligibilité"]),
                )
    section_end()


def render_subscription_page() -> None:
    context = st.session_state.get("subscription_context")
    section_start(tr("subscription_title"), tr("subscription_caption"))
    security_notice(tr("subscription_security_title"), tr("subscription_security_text"))

    if not context:
        st.info(tr("subscription_no_context"))
        section_end()
        return

    client = dict(context["client"])
    product = dict(context["product"])
    score = float(context.get("score", 0.0))

    session = st.session_state.get("subscription_session")
    if not session or session.get("product_name") != product.get("name"):
        session = initialize_subscription_session(client, product, score)
        st.session_state["subscription_session"] = session

    timeline(
        [
            tr("subscription_identity"),
            tr("subscription_product"),
            tr("subscription_summary"),
            tr("contract_block"),
            tr("subscription_status"),
        ],
        active_step=int(session.get("step", 1)),
    )
    section_end()

    section_start(tr("subscription_identity"))
    identity_cols = st.columns(3)
    with identity_cols[0]:
        code_client = st.text_input("Code Client", value=str(client.get("code_client", "")), disabled=True)
    with identity_cols[1]:
        nom = st.text_input(tr("client_last_name"), value=str(client.get("nom", "")))
    with identity_cols[2]:
        prenom = st.text_input(tr("client_first_name"), value=str(client.get("prenom", "")))

    valid_identity, missing_identity = validate_client_identity(code_client, nom, prenom)
    if not valid_identity:
        st.warning(f"Champs à compléter : {', '.join(missing_identity)}")
    client.update({"code_client": code_client, "nom": nom, "prenom": prenom})
    context["client"] = client
    st.session_state["subscription_context"] = context
    section_end()

    section_start(tr("subscription_product"))
    product_cols = st.columns([1, 1])
    with product_cols[0]:
        product_card(
            str(product.get("name", "")),
            get_product_icon(str(product.get("name", "")), str(product.get("category", ""))),
            score,
            f"Cluster {context.get('cluster_label', '-')}",
            category=str(product.get("category", "")),
            description=str(product.get("description", ""))[:220],
            benefits=list(product.get("benefits", [])),
            eligibility=list(product.get("eligibility", [])),
        )
    with product_cols[1]:
        channel = st.selectbox(tr("notification_channel"), ["Email", "SMS", "Push notification app mobile"])
        standard_price = st.text_input(tr("standard_price"), value=str(product.get("standard_price", "À définir")))
        promo_price = st.text_input(tr("promo_price"), value=str(product.get("promo_price", "Aucune promotion")))
        product.update({"standard_price": standard_price, "promo_price": promo_price})
        context["product"] = product
        st.session_state["subscription_context"] = context
    section_end()

    section_start(tr("subscription_summary"))
    summary_cols = st.columns(4)
    with summary_cols[0]:
        metric_card("Code Client", code_client, f"{prenom} {nom}".strip() or "-")
    with summary_cols[1]:
        metric_card(tr("product_detail"), product.get("name", "-"), product.get("category", "-"))
    with summary_cols[2]:
        metric_card(tr("chart_title"), f"{score:.1f}%", "NeuronAIze")
    with summary_cols[3]:
        metric_card(tr("notification_channel"), channel, tr("subscription_status"))

    if st.button(tr("generate_contract"), type="primary", use_container_width=True, disabled=not valid_identity):
        contract = generate_contract(client, product, {"standard_price": standard_price, "promo_price": promo_price})
        terms = generate_terms_and_conditions(product)
        st.session_state["subscription_contract"] = contract
        st.session_state["subscription_terms"] = terms
        st.session_state["subscription_contract_markdown"] = format_contract_as_markdown(contract, terms)
        st.session_state["subscription_session"]["step"] = 4
        st.rerun()
    section_end()

    contract_markdown = st.session_state.get("subscription_contract_markdown")
    if contract_markdown:
        section_start(tr("contract_block"))
        st.markdown(contract_markdown)
        st.download_button(
            "Télécharger le contrat simulé",
            data=contract_markdown.encode("utf-8"),
            file_name="contrat_souscription_simule_neuronaize.md",
            mime="text/markdown",
            use_container_width=True,
        )
        section_end()

        section_start(tr("campaign_validation"))
        status_badge(STATUS_PENDING, get_subscription_status_badge(STATUS_PENDING))
        st.info("Cette souscription est une simulation de démonstration et nécessite une validation bancaire finale.")
        confirm = st.button(tr("confirm_subscription"), type="primary", use_container_width=True)
        if confirm:
            subscription = create_subscription_request(
                client=client,
                product=product,
                score=score,
                contract_markdown=contract_markdown,
                terms_generated=True,
                channel=channel,
                status=STATUS_PENDING,
                comment="Demande créée depuis le workflow de souscription assistée NeuronAIze.",
            )
            st.session_state["subscriptions_table"] = save_subscription_to_excel(subscription)
            st.session_state["subscription_session"]["step"] = 5
            st.success(tr("subscription_saved"))
        section_end()


def render_subscription_reporting_page() -> None:
    subscriptions = load_subscriptions()
    section_start(tr("reporting_title"), tr("reporting_caption"))
    if subscriptions.empty:
        st.info(tr("no_subscriptions"))
        section_end()
        return

    kpis = compute_subscription_kpis(subscriptions)
    metric_cols = st.columns(5)
    with metric_cols[0]:
        metric_card(tr("total_subscriptions"), kpis["total"], "NeuronAIze")
    with metric_cols[1]:
        metric_card(tr("pending_subscriptions"), kpis["pending"], STATUS_PENDING)
    with metric_cols[2]:
        metric_card(tr("validated_subscriptions"), kpis["validated"], "Validation bancaire")
    with metric_cols[3]:
        metric_card(tr("products"), kpis["products"], tr("by_product"))
    with metric_cols[4]:
        metric_card(tr("potential_revenue"), kpis["potential_revenue"], "Démo")
    section_end()

    charts = build_subscription_charts(subscriptions)
    section_start("Analyse")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown(f"**{tr('by_product')}**")
        st.altair_chart(charts["product"], use_container_width=True)
        st.markdown(f"**{tr('by_status')}**")
        st.altair_chart(charts["status"], use_container_width=True)
    with chart_cols[1]:
        st.markdown(f"**{tr('by_date')}**")
        st.altair_chart(charts["date"], use_container_width=True)
        st.markdown(f"**{tr('by_category')}**")
        st.altair_chart(charts["category"], use_container_width=True)
    section_end()

    section_start("Tableau détaillé")
    st.dataframe(subscriptions, use_container_width=True, hide_index=True)
    st.download_button(
        tr("export_subscriptions"),
        data=export_subscriptions(subscriptions),
        file_name="reporting_souscriptions_neuronaize.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    section_end()


def render_agent_console_page() -> None:
    section_start(tr("agent_console_title"), tr("agent_console_caption"))
    hitl_mode = st.radio(
        tr("hitl_mode"),
        options=[tr("hitl_sync"), tr("hitl_exception"), tr("hitl_copilot")],
        index=0,
        horizontal=True,
    )

    report = st.session_state.get("workflow_report")
    notification_report = st.session_state.get("workflow_notification_report")
    events = get_agent_console_events()
    pending_count = 0
    if report is not None and not report.empty and "Statut" in report.columns:
        pending_count = int(report["Statut"].astype(str).str.contains("valider", case=False, na=False).sum())

    metric_cols = st.columns(4)
    with metric_cols[0]:
        metric_card(tr("executed_workflows"), events["Workflow"].nunique() if not events.empty else 0, hitl_mode)
    with metric_cols[1]:
        metric_card(tr("generated_recommendations"), len(report) if report is not None else 0, tr("ai_generated_proposals"))
    with metric_cols[2]:
        metric_card(tr("pending_validation_steps"), pending_count, tr("campaign_validation"))
    with metric_cols[3]:
        send_status = "Simulé" if notification_report is not None and not notification_report.empty else "Non lancé"
        metric_card(tr("simulated_send"), send_status, "Demo")
    section_end()

    if events.empty and (report is None or report.empty):
        section_start(tr("executed_workflows"))
        st.info(tr("no_agent_activity"))
        section_end()
        return

    section_start(tr("executed_workflows"))
    st.dataframe(events, use_container_width=True, hide_index=True)
    section_end()

    section_start(tr("execution_logs"))
    logs = build_console_logs()
    st.dataframe(logs, use_container_width=True, hide_index=True)
    section_end()

    section_start(tr("pending_validation_steps"))
    pending_rows = pd.DataFrame()
    if report is not None and not report.empty:
        if "Statut" in report.columns:
            pending_rows = report[report["Statut"].astype(str).str.contains("valider", case=False, na=False)]
        else:
            pending_rows = report
    if pending_rows.empty:
        st.success("Aucune étape en attente de validation.")
    else:
        st.dataframe(pending_rows, use_container_width=True, hide_index=True)
    section_end()

    section_start(tr("ai_generated_proposals"))
    if report is None or report.empty:
        st.info(tr("workflow_no_recommendation"))
        section_end()
        return

    editable_columns = [
        column
        for column in [
            "Code Client",
            "Cluster",
            "Produit recommandé",
            "Score de recommandation",
            "Canal proposé",
            "Message commercial proposé",
            "Offre associée",
            "Statut",
        ]
        if column in report.columns
    ]
    edited_report = st.data_editor(
        report[editable_columns],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="agent_console_proposals_editor",
    )

    action_cols = st.columns(3)
    with action_cols[0]:
        approve_clicked = st.button(tr("approve"), type="primary", use_container_width=True)
    with action_cols[1]:
        reject_clicked = st.button(tr("reject"), use_container_width=True)
    with action_cols[2]:
        modify_clicked = st.button(tr("modify_proposal"), use_container_width=True)

    if approve_clicked:
        approved = report.copy()
        approved["Statut"] = "Validé"
        st.session_state["workflow_report"] = approved
        st.session_state["workflow_campaign_validated"] = True
        log_agent_console_event("Approbation HITL", "Validé", f"Mode {hitl_mode}")
        st.success(tr("proposal_approved"))
        st.rerun()

    if reject_clicked:
        rejected = report.copy()
        rejected["Statut"] = "Rejeté"
        st.session_state["workflow_report"] = rejected
        st.session_state["workflow_campaign_validated"] = False
        log_agent_console_event("Rejet HITL", "Rejeté", f"Mode {hitl_mode}")
        st.warning(tr("proposal_rejected"))
        st.rerun()

    if modify_clicked:
        updated_report = report.copy()
        for column in edited_report.columns:
            updated_report[column] = edited_report[column]
        updated_report["Statut"] = "À valider"
        st.session_state["workflow_report"] = updated_report
        st.session_state["workflow_campaign_validated"] = False
        log_agent_console_event("Modification proposition", "À valider", f"Mode {hitl_mode}")
        st.success(tr("proposal_modified"))
        st.rerun()
    section_end()


def build_campaign_workflow_definition(require_human_validation: bool = True) -> WorkflowJSONDefinition:
    return WorkflowJSONDefinition(
        workflow_id="wf-campaign-guardrails",
        name="Contrôle conformité campagne NeuronAIze",
        entry_node_id="start",
        require_human_validation=require_human_validation,
        nodes=[
            WorkflowJSONNode(node_id="start", name="Démarrage", node_type="start"),
            WorkflowJSONNode(node_id="c1_recommendation", name="Recommandation", node_type="task", component="C1"),
            WorkflowJSONNode(node_id="c3_contract", name="Contrat simulé", node_type="task", component="C3"),
            WorkflowJSONNode(
                node_id="c4_signature",
                name="Signature simulée",
                node_type="task",
                component="C4",
                critical_action="create_subscription",
                requires_human_validation=require_human_validation,
            ),
            WorkflowJSONNode(
                node_id="c9_accounting",
                name="Comptabilité simulée",
                node_type="task",
                component="C9",
                critical_action="export_sensitive_data",
                requires_human_validation=require_human_validation,
            ),
            WorkflowJSONNode(node_id="end", name="Fin", node_type="end"),
        ],
        edges=[
            WorkflowJSONEdge(edge_id="e1", source_node_id="start", target_node_id="c1_recommendation"),
            WorkflowJSONEdge(edge_id="e2", source_node_id="c1_recommendation", target_node_id="c3_contract"),
            WorkflowJSONEdge(edge_id="e3", source_node_id="c3_contract", target_node_id="c4_signature"),
            WorkflowJSONEdge(edge_id="e4", source_node_id="c4_signature", target_node_id="c9_accounting"),
            WorkflowJSONEdge(edge_id="e5", source_node_id="c9_accounting", target_node_id="end"),
        ],
    )


def render_workflow_agent_page(sidebar_client_file) -> None:
    section_start(tr("workflow_agent_title"), tr("workflow_agent_caption"))
    st.session_state["active_workflow_name"] = st.session_state.get(
        "active_workflow_name",
        "Campagne cross-selling NeuronAIze",
    )

    st.markdown(
        """
        **Timeline**

        `1. Planification` → `2. Chargement sources` → `3. Scoring clients` → `4. Rapport brouillon`
        → `5. Validation humaine` → `6. Notifications simulées`
        """
    )
    section_end()

    section_start(tr("planning"))
    planning_cols = st.columns([2, 1, 1, 1, 1])
    with planning_cols[0]:
        workflow_name = st.text_input(tr("workflow_name"), value="Campagne cross-selling NeuronAIze")
        st.session_state["active_workflow_name"] = workflow_name
    with planning_cols[1]:
        execution_frequency = st.selectbox(tr("frequency"), [tr("daily"), tr("weekly"), tr("monthly")], index=2)
    with planning_cols[2]:
        day_of_month = st.number_input(tr("day_of_month"), min_value=1, max_value=31, value=5, step=1)
    with planning_cols[3]:
        execution_time_value = st.time_input(tr("execution_time"), value=time(8, 0))
    with planning_cols[4]:
        workflow_enabled = st.toggle(tr("workflow_enabled"), value=True)
    section_end()

    section_start(tr("data_sources"))
    source_cols = st.columns(4)
    with source_cols[0]:
        workflow_client_file = st.file_uploader(
            tr("client_source"),
            type=["xlsx", "xls"],
            key="workflow_client_upload",
        )
        effective_client_file = workflow_client_file or sidebar_client_file
        if effective_client_file is None:
            st.warning(tr("workflow_no_client_file"))
    with source_cols[1]:
        workflow_catalog_file = st.file_uploader(
            tr("catalog_source"),
            type=["xlsx", "xls"],
            key="workflow_catalog_upload",
        )
        workflow_catalog = st.session_state.get("product_catalog")
        if workflow_catalog_file is not None:
            try:
                raw_catalog = load_catalog(workflow_catalog_file)
                missing = validate_catalog(raw_catalog)
                if missing:
                    st.error(f"{tr('catalog_missing')} : {', '.join(missing)}")
                else:
                    workflow_catalog = prepare_catalog(raw_catalog)
                    st.session_state["product_catalog"] = workflow_catalog
                    st.session_state["product_rag_index"] = build_product_rag_index(workflow_catalog)
                    st.success(tr("catalog_valid"))
            except Exception as exc:
                st.error(f"{tr('read_error')} : {exc}")
        elif workflow_catalog is None:
            st.info(tr("workflow_catalog_missing"))
        else:
            st.success(tr("catalog_valid"))
    with source_cols[2]:
        workflow_promotion_file = st.file_uploader(
            tr("promotion_source"),
            type=["xlsx", "xls"],
            key="workflow_promotion_upload",
        )
        if workflow_promotion_file is not None:
            try:
                workflow_promotions = prepare_promotions(load_excel(workflow_promotion_file))
                st.session_state["workflow_promotions"] = save_promotions(workflow_promotions)
                st.success(f"{tr('active_promotions')} : {int(workflow_promotions['Campagne active'].sum())}")
            except Exception as exc:
                st.error(f"{tr('read_error')} : {exc}")
        else:
            workflow_promotions = st.session_state.get("workflow_promotions")
            if workflow_promotions is None:
                workflow_promotions = load_promotions()
                st.session_state["workflow_promotions"] = workflow_promotions
    with source_cols[3]:
        workflow_rules_file = st.file_uploader(
            tr("rules_source"),
            type=["xlsx", "xls", "csv"],
            key="workflow_rules_upload",
        )
        rules_loaded = workflow_rules_file is not None
        if rules_loaded:
            st.success(tr("rules_help_title"))
    section_end()

    workflow_recommender = None
    workflow_data = None
    cluster_options: list[int] = []

    if effective_client_file is not None:
        try:
            workflow_data = load_excel(effective_client_file)
            if workflow_data.empty:
                st.error(tr("empty_file"))
            elif not detect_product_columns(workflow_data):
                st.error(tr("missing_products"))
            else:
                signature = (
                    getattr(effective_client_file, "name", "uploaded"),
                    len(workflow_data),
                    tuple(workflow_data.columns),
                    "workflow",
                )
                if st.session_state.get("workflow_recommender_signature") != signature:
                    with st.spinner(tr("analysis_spinner")):
                        workflow_recommender = BankingRecommender(
                            threshold=0.30,
                            min_clusters=AUTO_CLUSTER_MIN,
                            max_clusters=AUTO_CLUSTER_SEARCH_LIMIT,
                        ).fit(workflow_data)
                        st.session_state["workflow_recommender"] = workflow_recommender
                        st.session_state["workflow_recommender_signature"] = signature
                else:
                    workflow_recommender = st.session_state.get("workflow_recommender")

                if workflow_recommender is not None:
                    cluster_options = sorted(
                        workflow_recommender.training_data_["_cluster"].dropna().astype(int).unique().tolist()
                    )
        except Exception as exc:
            st.error(f"{tr('analysis_error')} : {exc}")

    section_start(tr("recommendation_rules"))
    rule_cols = st.columns(4)
    with rule_cols[0]:
        recommendation_threshold = st.slider(
            tr("threshold"),
            min_value=0.05,
            max_value=0.90,
            value=0.30,
            step=0.05,
            key="workflow_threshold",
        )
    with rule_cols[1]:
        max_products_per_client = st.number_input(
            tr("max_products_client"),
            min_value=1,
            max_value=10,
            value=2,
            step=1,
        )
    with rule_cols[2]:
        exclude_owned = st.checkbox(tr("exclude_owned"), value=True, disabled=True)
    with rule_cols[3]:
        require_human_validation = st.toggle(tr("human_validation"), value=True)

    excluded_clusters = st.multiselect(tr("exclude_clusters"), options=cluster_options, default=[])
    expert_weight = st.slider(
        tr("expert_weight"),
        min_value=0.0,
        max_value=0.50,
        value=0.0,
        step=0.05,
        help="0.10 ajoute 10 % au score de recommandation pour simuler une pondération experte.",
    )

    st.markdown(f"**{tr('rules_help_title')}**")
    help_cols = st.columns(5)
    with help_cols[0]:
        help_card(tr("rules_help_score"), tr("rules_help_score_text"))
    with help_cols[1]:
        help_card(tr("rules_help_max"), tr("rules_help_max_text"))
    with help_cols[2]:
        help_card(tr("rules_help_owned"), tr("rules_help_owned_text"))
    with help_cols[3]:
        help_card(tr("rules_help_validation"), tr("rules_help_validation_text"))
    with help_cols[4]:
        help_card(tr("rules_help_clusters"), tr("rules_help_clusters_text"))
    section_end()

    section_start("Garde-fous conformité")
    compliance_workflow = build_campaign_workflow_definition(require_human_validation=require_human_validation)
    compliance_result = check_workflow_compliance(compliance_workflow)
    violations = compliance_result["violations"]
    guardrail_cols = st.columns(3)
    with guardrail_cols[0]:
        metric_card("Statut conformité", "OK" if compliance_result["is_compliant"] else "Bloqué", "Workflow")
    with guardrail_cols[1]:
        metric_card("Erreurs", compliance_result["blocking_errors"], "Garde-fous")
    with guardrail_cols[2]:
        metric_card("Warnings", compliance_result["warnings"], "Contrôle")

    if violations:
        st.error("Des erreurs de conformité bloquent ce workflow.")
        st.dataframe(violations_to_dataframe(violations), use_container_width=True, hide_index=True)
    else:
        st.success("Aucune erreur de conformité détectée.")
    section_end()

    section_start(tr("offers"))
    offer_cols = st.columns(6)
    with offer_cols[0]:
        standard_price = st.text_input(tr("standard_price"), value="À définir")
    with offer_cols[1]:
        promo_price = st.text_input(tr("promo_price"), value="Offre personnalisée")
    with offer_cols[2]:
        offer_start = st.date_input(tr("offer_start"))
    with offer_cols[3]:
        offer_end = st.date_input(tr("offer_end"))
    with offer_cols[4]:
        promo_message = st.text_area(tr("promo_message"), value="Offre réservée aux clients éligibles.")
    with offer_cols[5]:
        product_campaign_active = st.toggle(tr("product_campaign_active"), value=True)

    product_source_options = []
    if workflow_recommender is not None:
        product_source_options = list(workflow_recommender.product_columns)
    elif workflow_catalog is not None and "Colonne source bddf2" in workflow_catalog.columns:
        product_source_options = workflow_catalog["Colonne source bddf2"].dropna().astype(str).tolist()

    promotion_cols = st.columns([2, 1])
    with promotion_cols[0]:
        selected_promotion_product = st.selectbox(
            tr("product_source_column"),
            options=product_source_options or [""],
            format_func=lambda value: catalog_display_name(value, get_catalog_product(workflow_catalog, value)),
        )
    with promotion_cols[1]:
        if st.button(tr("save_promotion"), use_container_width=True):
            if selected_promotion_product:
                workflow_promotions = upsert_promotion(
                    st.session_state.get("workflow_promotions"),
                    {
                        "Colonne source bddf2": selected_promotion_product,
                        "Nom produit": catalog_display_name(
                            selected_promotion_product,
                            get_catalog_product(workflow_catalog, selected_promotion_product),
                        ),
                        "Prix standard": standard_price,
                        "Prix promotionnel": promo_price,
                        "Date début": offer_start,
                        "Date fin": offer_end,
                        "Message promotionnel": promo_message,
                        "Campagne active": product_campaign_active,
                    },
                )
                st.session_state["workflow_promotions"] = save_promotions(workflow_promotions)
                st.success(tr("promotions_saved"))

    workflow_promotions = st.session_state.get("workflow_promotions", load_promotions())
    if workflow_promotions is not None and not workflow_promotions.empty:
        st.dataframe(workflow_promotions, use_container_width=True, hide_index=True)
        st.download_button(
            tr("export_excel"),
            data=export_promotions(workflow_promotions),
            file_name="promotions_neuronaize.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    section_end()

    section_start(tr("channels"))
    selected_channels = st.multiselect(
        tr("channels"),
        options=[tr("email"), tr("sms"), tr("push"), tr("advisor_call")],
        default=[tr("email")],
    )
    if not selected_channels:
        st.warning(tr("channels"))
    section_end()

    config = create_workflow_config(
        workflow_name=workflow_name,
        execution_frequency=execution_frequency,
        day_of_month=int(day_of_month),
        execution_time=execution_time_value.strftime("%H:%M"),
        workflow_enabled=workflow_enabled,
        recommendation_threshold=float(recommendation_threshold),
        max_products_per_client=int(max_products_per_client),
        selected_channels=selected_channels or [tr("email")],
        require_human_validation=require_human_validation,
        campaign_status=tr("draft"),
        excluded_clusters=excluded_clusters,
        expert_weight=float(expert_weight),
    )
    offer_config = {
        "standard_price": standard_price,
        "promo_price": promo_price,
        "start_date": offer_start,
        "end_date": offer_end,
        "promo_message": promo_message,
    }

    section_start(tr("simulation"))
    sim_cols = st.columns(4)
    with sim_cols[0]:
        metric_card(tr("clients"), len(workflow_data) if workflow_data is not None else 0, tr("client_source"))
    with sim_cols[1]:
        metric_card(tr("products"), len(detect_product_columns(workflow_data)) if workflow_data is not None else 0, "Produit -")
    with sim_cols[2]:
        active_promotions = int(workflow_promotions["Campagne active"].sum()) if workflow_promotions is not None and not workflow_promotions.empty else 0
        metric_card(tr("active_promotions"), active_promotions, tr("offers"))
    with sim_cols[3]:
        metric_card(tr("human_validation"), "ON" if require_human_validation else "OFF", tr("campaign_validation"))

    if st.button(tr("simulate_workflow"), type="primary", use_container_width=True):
        if workflow_recommender is None or workflow_data is None:
            st.error(tr("workflow_no_client_file"))
        else:
            st.session_state["workflow_simulation"] = simulate_workflow(
                config,
                client_count=len(workflow_data),
                product_count=len(detect_product_columns(workflow_data)),
                promotion_count=active_promotions,
                rules_loaded=rules_loaded,
            )
            st.session_state["workflow_timeline"] = pd.DataFrame(workflow_timeline_rows())
            log_agent_console_event(
                "Simulation workflow",
                "Prêt pour validation" if require_human_validation else "Simulé",
                f"{len(workflow_data)} clients analysés",
            )

    if st.session_state.get("workflow_simulation"):
        st.dataframe(pd.DataFrame([st.session_state["workflow_simulation"]]), use_container_width=True, hide_index=True)
    if st.session_state.get("workflow_timeline") is not None:
        st.markdown(f"**{tr('workflow_timeline')}**")
        st.dataframe(st.session_state["workflow_timeline"], use_container_width=True, hide_index=True)
    section_end()

    section_start(tr("generated_report"))
    if st.button(tr("generate_report"), type="primary", use_container_width=True):
        if workflow_recommender is None:
            st.error(tr("workflow_no_client_file"))
        else:
            try:
                report = generate_recommendation_report(
                    workflow_recommender,
                    workflow_catalog,
                    config,
                    offer_config,
                    promotions=workflow_promotions,
                )
                if report.empty:
                    st.warning(tr("workflow_no_recommendation"))
                st.session_state["workflow_report"] = report
                st.session_state["workflow_campaign_validated"] = False
                log_agent_console_event(
                    "Génération rapport",
                    "À valider" if require_human_validation else "Brouillon",
                    f"{len(report)} recommandations générées",
                )
            except Exception as exc:
                st.error(f"{tr('recommendation_error')} : {exc}")

    report = st.session_state.get("workflow_report")
    if report is not None and not report.empty:
        campaign_kpis = compute_campaign_kpis(report)
        perf_cols = st.columns(4)
        with perf_cols[0]:
            metric_card(tr("targeted_clients"), campaign_kpis["targeted_clients"], tr("clients"))
        with perf_cols[1]:
            metric_card(tr("generated_recommendations"), campaign_kpis["recommendations"], tr("generated_report"))
        with perf_cols[2]:
            metric_card(tr("products"), campaign_kpis["products"], tr("top_products"))
        with perf_cols[3]:
            metric_card(tr("pending_campaigns"), campaign_kpis["pending_validation"], tr("campaign_validation"))

        campaign_charts = build_campaign_charts(report)
        if campaign_charts:
            chart_cols = st.columns(2)
            with chart_cols[0]:
                if "products" in campaign_charts:
                    st.markdown(f"**{tr('top_products')}**")
                    st.altair_chart(campaign_charts["products"], use_container_width=True)
                if "status" in campaign_charts:
                    st.markdown(f"**{tr('pending_campaigns')}**")
                    st.altair_chart(campaign_charts["status"], use_container_width=True)
            with chart_cols[1]:
                if "clusters" in campaign_charts:
                    st.markdown(f"**{tr('targeted_segments')}**")
                    st.altair_chart(campaign_charts["clusters"], use_container_width=True)

        st.dataframe(report, use_container_width=True, hide_index=True)
        st.download_button(
            tr("export_excel"),
            data=report_to_excel_bytes(report),
            file_name="rapport_campagne_neuronaize.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    section_end()

    section_start(tr("campaign_validation"))
    st.info(tr("workflow_agent_caption"))
    validation_cols = st.columns(2)
    with validation_cols[0]:
        validate_clicked = st.button(tr("validate_campaign"), type="primary", use_container_width=True)
    with validation_cols[1]:
        simulate_send_clicked = st.button(tr("simulated_send"), use_container_width=True)

    if validate_clicked:
        report = st.session_state.get("workflow_report")
        if report is None or report.empty:
            st.error(tr("workflow_no_recommendation"))
        else:
            st.session_state["workflow_report"] = validate_campaign(report, require_human_validation)
            st.session_state["workflow_campaign_validated"] = True
            log_agent_console_event("Validation campagne", "Validé", f"{len(report)} lignes approuvées")
            st.success(tr("workflow_validated"))

    if simulate_send_clicked:
        report = st.session_state.get("workflow_report")
        if report is None or report.empty:
            st.error(tr("workflow_no_recommendation"))
        else:
            simulated_report = simulate_notifications(
                report,
                require_human_validation=require_human_validation,
                campaign_validated=st.session_state.get("workflow_campaign_validated", False),
            )
            st.session_state["workflow_notification_report"] = simulated_report
            log_agent_console_event(
                "Simulation envoi",
                "Simulé" if st.session_state.get("workflow_campaign_validated", False) else "À valider",
                f"{len(simulated_report)} notifications préparées",
            )

    if st.session_state.get("workflow_notification_report") is not None:
        st.dataframe(st.session_state["workflow_notification_report"], use_container_width=True, hide_index=True)
    section_end()


def reset_downstream_state() -> None:
    for key in ["customer", "recommendations", "selected_product", "chat_messages"]:
        st.session_state.pop(key, None)


inject_premium_css()

render_header(
    LOGO_PATH,
    tr("title"),
    tr("subtitle"),
    {"fr": TRANSLATIONS["fr"]["fr"], "en": TRANSLATIONS["en"]["en"]},
)

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_column_width=True)
        st.divider()

    st.header(tr("screen"))
    screen = st.radio(
        tr("screen"),
        options=["engine", "catalog", "workflow", "agent_console", "subscription", "reporting"],
        format_func=lambda value: {
            "engine": tr("screen_engine"),
            "catalog": tr("screen_catalog"),
            "workflow": tr("screen_workflow"),
            "agent_console": tr("screen_agent_console"),
            "subscription": tr("screen_subscription"),
            "reporting": tr("screen_reporting"),
        }[value],
        label_visibility="collapsed",
        key="screen",
    )

    st.header(tr("data"))
    uploaded_file = st.file_uploader(tr("upload"), type=["xlsx", "xls"])
    sidebar_catalog_file = st.file_uploader(
        tr("catalog_sidebar_upload"),
        type=["xlsx", "xls"],
        key="sidebar_catalog_upload",
    )
    if sidebar_catalog_file is not None and register_uploaded_catalog(sidebar_catalog_file, source="sidebar"):
        catalog = st.session_state.get("product_catalog")
        row_count = len(catalog) if catalog is not None else 0
        st.success(f"{tr('catalog_loaded')} : {row_count}")

    st.header(tr("settings"))
    threshold = st.slider(
        tr("threshold"),
        min_value=0.05,
        max_value=0.90,
        value=0.30,
        step=0.05,
        help=tr("threshold_help"),
    )
    min_clusters = st.slider(
        tr("min_clusters"),
        min_value=2,
        max_value=AUTO_CLUSTER_SEARCH_LIMIT,
        value=AUTO_CLUSTER_MIN,
        step=1,
        help=tr("min_clusters_help"),
    )
    max_clusters = st.slider(
        tr("max_clusters"),
        min_value=min_clusters,
        max_value=AUTO_CLUSTER_SEARCH_LIMIT,
        value=AUTO_CLUSTER_SEARCH_LIMIT,
        step=1,
        help=tr("max_clusters_help"),
    )

    st.header(tr("workflow"))
    for step_key in ["step_1", "step_2", "step_3", "step_4", "step_5", "step_6", "step_7"]:
        badge(tr(step_key))


if screen == "catalog":
    render_catalog_page()
    st.stop()

if screen == "workflow":
    render_workflow_agent_page(uploaded_file)
    st.stop()

if screen == "agent_console":
    render_agent_console_page()
    st.stop()

if screen == "subscription":
    render_subscription_page()
    st.stop()

if screen == "reporting":
    render_subscription_reporting_page()
    st.stop()


if uploaded_file is None:
    section_start(tr("title"), tr("no_file"))
    cols = st.columns(4)
    with cols[0]:
        metric_card("Excel", "Upload", "0/1 products")
    with cols[1]:
        metric_card("KMedoids", "Manhattan", "Automatic clusters")
    with cols[2]:
        metric_card("NeuronAIze", "Scoring", "Similar clients")
    with cols[3]:
        metric_card("Advisor", "Action", "Product detail")
    if st.session_state.get("product_catalog") is None:
        st.info(tr("catalog_not_loaded"))
    section_end()
    st.stop()

try:
    data = load_excel(uploaded_file)
except Exception as exc:
    st.error(f"{tr('read_error')} : {exc}")
    st.stop()

if data.empty:
    st.error(tr("empty_file"))
    st.stop()

product_columns = detect_product_columns(data)
client_code_column = find_client_code_column(data)

if not product_columns:
    st.error(tr("missing_products"))
    st.stop()

analysis_signature = (uploaded_file.name, len(data), tuple(data.columns), threshold, min_clusters, max_clusters)
if st.session_state.get("analysis_signature") != analysis_signature:
    reset_downstream_state()
    with st.spinner(tr("analysis_spinner")):
        try:
            recommender = BankingRecommender(
                threshold=threshold,
                min_clusters=min_clusters,
                max_clusters=max_clusters,
            )
            recommender.fit(data)
            st.session_state["recommender"] = recommender
            st.session_state["analysis_signature"] = analysis_signature
        except Exception as exc:
            st.error(f"{tr('analysis_error')} : {exc}")
            st.stop()

recommender: BankingRecommender = st.session_state["recommender"]
product_catalog = st.session_state.get("product_catalog")
product_rag_index = st.session_state.get("product_rag_index")
summary = recommender.cluster_summary_
display_summary = display_cluster_summary(summary)

section_start(tr("cluster_title"), tr("cluster_caption"))
metric_cols = st.columns(4)
with metric_cols[0]:
    metric_card(tr("clients"), len(data), uploaded_file.name)
with metric_cols[1]:
    metric_card(tr("clusters"), recommender.selected_n_clusters_, "Elbow inertia")
with metric_cols[2]:
    metric_card(tr("products"), len(product_columns), "Produit -")
with metric_cols[3]:
    metric_card(tr("code_column"), client_code_column or "-", "Première colonne")

st.markdown(f"**{tr('inertia_title')}**")
st.caption(tr("inertia_caption"))
diagnostic_cols = st.columns([1, 1, 2])
with diagnostic_cols[0]:
    metric_card(tr("selected_k"), recommender.selected_n_clusters_, tr("clusters"))
with diagnostic_cols[1]:
    metric_card(tr("selection_method"), recommender.cluster_selection_method_ or "-", "KMedoids")
with diagnostic_cols[2]:
    if recommender.inertia_diagnostics_ is not None:
        st.dataframe(
            recommender.inertia_diagnostics_,
            use_container_width=True,
            hide_index=True,
        )

if recommender.inertia_diagnostics_ is not None:
    st.markdown(f"**{tr('inertia_curve')}**")
    inertia_chart(recommender.inertia_diagnostics_, int(recommender.selected_n_clusters_))

chart_col, summary_col = st.columns([1, 1.8])
with chart_col:
    st.markdown(f"**{tr('cluster_size')}**")
    cluster_size = summary[["Cluster", "Nombre de personnes"]].rename(
        columns={"Nombre de personnes": tr("clients")}
    )
    st.bar_chart(cluster_size.set_index("Cluster"))

with summary_col:
    st.markdown(f"**{tr('summary')}**")
    st.dataframe(display_summary, use_container_width=True, hide_index=True)

st.markdown(f"**{tr('dominant_profile')}**")
profile_cols = st.columns(min(3, len(summary)))
for idx, (_, row) in enumerate(display_summary.iterrows()):
    with profile_cols[idx % len(profile_cols)]:
        metric_card(f"Cluster {row['Cluster']}", row[tr("profile_label")] if tr("profile_label") in row else row.get("Libellé automatique", "-"), f"{row.get('Nombre de personnes', row.get(tr('clients'), '-'))} clients")

search_col, button_col = st.columns([3, 1], vertical_alignment="bottom")
with search_col:
    client_code = st.text_input(
        tr("enter_code"),
        value="",
        placeholder=normalize_client_code(data.iloc[0, 0]),
    )
with button_col:
    validate_client = st.button(tr("validate"), use_container_width=True)
section_end()

with st.expander(tr("preview")):
    st.dataframe(data.head(20), use_container_width=True)

if validate_client:
    try:
        st.session_state["customer"] = recommender.get_customer_by_code(client_code)
        st.session_state.pop("recommendations", None)
        st.session_state.pop("selected_product", None)
        st.session_state.pop("chat_messages", None)
    except Exception as exc:
        st.error(f"{tr('client_error')} : {exc}")

customer_df: pd.DataFrame | None = st.session_state.get("customer")
if customer_df is None:
    st.stop()

customer_row = customer_df.iloc[0]
section_start(tr("client_title"), tr("client_caption"))
client_fields = preferred_client_fields(customer_row, recommender.feature_columns, recommender.client_code_column)
client_field_grid(client_fields)

st.markdown(f"**{tr('owned_products')}**")
owned = owned_products(customer_row, recommender.product_columns)
if not owned:
    st.info(tr("no_owned_products"))
else:
    product_cols = st.columns(min(4, len(owned)))
    for idx, product in enumerate(owned):
        with product_cols[idx % len(product_cols)]:
            product_card(clean_product_name(product), get_product_icon(product))

if st.button(tr("analyze"), type="primary", use_container_width=True):
    try:
        recommendations = recommender.recommend(customer_df, threshold=threshold)
        st.session_state["recommendations"] = recommendations
        st.session_state.pop("selected_product", None)
        st.session_state.pop("chat_messages", None)
    except Exception as exc:
        st.error(f"{tr('recommendation_error')} : {exc}")
section_end()

recommendations: pd.DataFrame | None = st.session_state.get("recommendations")
if recommendations is None:
    st.stop()

predicted_cluster = recommender.predict_cluster(customer_df)
cluster_label = summary.loc[summary["Cluster"] == predicted_cluster, "Libellé automatique"].iloc[0]
if st.session_state["language"] == "en":
    cluster_label = translate_cluster_label(cluster_label)

section_start(tr("recommendations_title"), tr("recommendations_caption"))
if product_catalog is None:
    st.info(tr("catalog_not_loaded"))
metric_cols = st.columns(3)
with metric_cols[0]:
    metric_card("Cluster", predicted_cluster, cluster_label)
with metric_cols[1]:
    metric_card(tr("threshold"), f"{threshold * 100:.0f}%", "Minimum")
with metric_cols[2]:
    metric_card(tr("products"), len(recommendations), tr("recommendations_title"))

if recommendations.empty:
    st.info(tr("no_recommendations"))
else:
    rec_cols = st.columns(min(3, len(recommendations)))
    for idx, recommendation in recommendations.iterrows():
        product = recommendation["Produit"]
        score = float(recommendation["Score %"])
        source = f"{int(recommendation['Clients similaires'])} {tr('similar_customers')}"
        catalog_product = get_catalog_product(product_catalog, product)
        display_name = catalog_display_name(product, catalog_product)
        category = str(catalog_product.get("Catégorie", "")) if catalog_product else ""
        description = str(catalog_product.get("Description", "")) if catalog_product else ""
        benefits = split_catalog_field(catalog_product.get("Avantages", "")) if catalog_product else []
        eligibility = (
            split_catalog_field(catalog_product.get("Conditions d’éligibilité", ""))
            if catalog_product
            else []
        )
        with rec_cols[idx % len(rec_cols)]:
            product_card(
                display_name,
                get_product_icon(product, category),
                score,
                source,
                category=category,
                description=description[:180],
                benefits=benefits,
                eligibility=eligibility,
            )
            if st.button(tr("details"), key=f"detail_{idx}", use_container_width=True):
                st.session_state["selected_product"] = product
                st.session_state["selected_score"] = score
                st.session_state["chat_messages"] = []

    st.markdown(f"**{tr('chart_title')}**")
    recommendation_chart(recommendations)
section_end()

selected_product = st.session_state.get("selected_product")
if not selected_product:
    st.stop()

selected_score = float(st.session_state.get("selected_score", 0.0))
selected_catalog_product = get_catalog_product(product_catalog, selected_product)
details = get_product_details(selected_product, selected_score, cluster_label, selected_catalog_product)

section_start(tr("product_detail"), details["description"])
if product_catalog is not None and selected_catalog_product is None:
    st.warning(tr("catalog_product_not_found"))
detail_cols = st.columns([1, 1])
with detail_cols[0]:
    product_card(
        details["name"],
        get_product_icon(selected_product, details.get("category", "")),
        selected_score,
        f"Cluster {predicted_cluster}",
        category=details.get("category", ""),
    )
    if details.get("category"):
        badge(f"{tr('category')} : {details['category']}")
    st.markdown(f"**{tr('why')}**")
    st.write(details["why"])
    if st.button(tr("subscription_button"), type="primary", use_container_width=True):
        st.session_state["subscription_context"] = build_subscription_context(
            customer_row,
            recommender,
            selected_product,
            selected_score,
            cluster_label,
            selected_catalog_product,
        )
        for key in ["subscription_session", "subscription_contract", "subscription_terms", "subscription_contract_markdown"]:
            st.session_state.pop(key, None)
        st.session_state["screen"] = "subscription"
        st.rerun()
with detail_cols[1]:
    if details.get("eligibility"):
        detail_card(tr("eligibility"), details["eligibility"])
    detail_card(tr("benefits"), details["benefits"])
    detail_card(tr("limits"), details["limits"])
    detail_card(tr("sales"), details["sales_arguments"])
section_end()

section_start(tr("chatbot"), tr("chat_intro"))
if product_catalog is not None:
    st.info(tr("catalog_chat_strict"))
messages = st.session_state.setdefault("chat_messages", [])
for message in messages:
    chat_message(message["role"], message["content"])

question_col, send_col = st.columns([4, 1], vertical_alignment="bottom")
with question_col:
    question = st.text_input(tr("chat_placeholder"), key="chat_question")
with send_col:
    send_message = st.button(tr("send"), use_container_width=True)

if send_message and question.strip():
    response = answer_product_question(
        question,
        selected_product,
        selected_score,
        cluster_label,
        st.session_state["language"],
        catalog_product=selected_catalog_product,
        rag_index=product_rag_index,
    )
    messages.append({"role": "user", "content": question})
    messages.append({"role": "bot", "content": response})
    st.rerun()
section_end()
