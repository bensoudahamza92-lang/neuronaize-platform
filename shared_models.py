from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Channel = Literal["Email", "SMS", "Push notification app mobile"]
SubscriptionStatus = Literal[
    "Brouillon",
    "En attente de validation",
    "Validée",
    "Rejetée",
    "Contrat généré",
]
CampaignStatus = Literal["Brouillon", "À valider", "Validé", "Rejeté", "Envoyé simulé"]
WorkflowNodeType = Literal["start", "task", "decision", "human_validation", "notification", "end"]
ExecutionStatus = Literal["success", "warning", "error", "skipped"]


class ClientProfile(BaseModel):
    client_code: str = Field(..., description="Unique customer identifier from the first Excel column.")
    last_name: str | None = None
    first_name: str | None = None
    cluster_id: int | None = None
    cluster_label: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)
    owned_products: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductCatalogItem(BaseModel):
    product_code: str
    product_name: str
    source_column: str = Field(..., description='Column name in the customer base, usually starting with "Produit -".')
    category: str
    description: str = ""
    eligibility_conditions: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    sales_arguments: list[str] = Field(default_factory=list)
    chatbot_keywords: list[str] = Field(default_factory=list)
    icon: str | None = None
    standard_price: str | None = None
    promotional_price: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationResult(BaseModel):
    client_code: str
    product: ProductCatalogItem | None = None
    product_source_column: str
    product_name: str
    cluster_id: int
    score_percent: float = Field(..., ge=0, le=100)
    similar_customers_count: int = Field(default=0, ge=0)
    source: str = ""
    reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SubscriptionRequest(BaseModel):
    subscription_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    client: ClientProfile
    product: ProductCatalogItem
    recommendation_score_percent: float = Field(..., ge=0, le=100)
    channel: Channel = "Email"
    status: SubscriptionStatus = "En attente de validation"
    contract_generated: bool = False
    terms_generated: bool = False
    final_validation: bool = False
    comment: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    workflow_id: str
    current_node_id: str | None = None
    status: Literal["draft", "running", "waiting_validation", "completed", "failed"] = "draft"
    variables: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[RecommendationResult] = Field(default_factory=list)
    started_at: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None


class WorkflowNode(BaseModel):
    node_id: str
    name: str
    node_type: WorkflowNodeType = "task"
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    requires_human_validation: bool = False


class WorkflowEdge(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    condition: str | None = None
    label: str | None = None


class WorkflowDefinition(BaseModel):
    workflow_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    entry_node_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CampaignConfig(BaseModel):
    campaign_id: str
    workflow_name: str
    execution_frequency: Literal["Chaque jour", "Chaque semaine", "Chaque mois"] = "Chaque mois"
    day_of_month: int | None = Field(default=5, ge=1, le=31)
    recommendation_threshold: float = Field(default=0.30, ge=0, le=1)
    max_products_per_client: int = Field(default=2, ge=1)
    selected_channels: list[Channel] = Field(default_factory=lambda: ["Email"])
    excluded_clusters: list[int] = Field(default_factory=list)
    exclude_already_owned_products: bool = True
    require_human_validation: bool = True
    standard_price: str | None = None
    promotional_price: str | None = None
    offer_start_date: str | None = None
    offer_end_date: str | None = None
    promotional_message: str = ""
    campaign_status: CampaignStatus = "Brouillon"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionLog(BaseModel):
    log_id: str
    workflow_id: str | None = None
    campaign_id: str | None = None
    node_id: str | None = None
    status: ExecutionStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.now)
    duration_ms: int | None = Field(default=None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)
