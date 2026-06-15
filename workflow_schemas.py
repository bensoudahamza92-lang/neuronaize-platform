from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from shared_models import WorkflowDefinition, WorkflowEdge, WorkflowNode


NodeComponent = Literal["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"]
CriticalAction = Literal["send_notification", "validate_campaign", "create_subscription", "export_sensitive_data"]


class WorkflowJSONNode(WorkflowNode):
    component: NodeComponent | None = None
    critical_action: CriticalAction | None = None
    enabled: bool = True


class WorkflowJSONEdge(WorkflowEdge):
    condition: str | None = None
    condition_config: dict[str, Any] = Field(default_factory=dict)


class WorkflowJSONDefinition(WorkflowDefinition):
    nodes: list[WorkflowJSONNode] = Field(default_factory=list)
    edges: list[WorkflowJSONEdge] = Field(default_factory=list)
    require_human_validation: bool = True
    stop_on_error: bool = True


def workflow_json_schema() -> dict[str, Any]:
    return WorkflowJSONDefinition.model_json_schema()


def parse_workflow_json(payload: dict[str, Any]) -> WorkflowJSONDefinition:
    return WorkflowJSONDefinition.model_validate(payload)
