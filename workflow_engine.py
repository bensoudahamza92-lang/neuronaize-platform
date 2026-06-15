from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared_models import WorkflowState
from workflow_executor import WorkflowExecutionResult, execute_workflow_definition
from workflow_schemas import WorkflowJSONDefinition, parse_workflow_json


def load_workflow_json(path: str | Path) -> WorkflowJSONDefinition:
    with Path(path).open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return parse_workflow_json(payload)


def load_workflow_from_dict(payload: dict[str, Any]) -> WorkflowJSONDefinition:
    return parse_workflow_json(payload)


def execute_workflow_json(
    workflow_payload: dict[str, Any] | str | Path,
    initial_state: WorkflowState | None = None,
    component_registry: dict[str, object] | None = None,
) -> WorkflowExecutionResult:
    if isinstance(workflow_payload, (str, Path)):
        workflow = load_workflow_json(workflow_payload)
    else:
        workflow = load_workflow_from_dict(workflow_payload)

    return execute_workflow_definition(
        workflow,
        initial_state=initial_state,
        component_registry=component_registry,
    )


def workflow_logs_as_dicts(result: WorkflowExecutionResult) -> list[dict[str, Any]]:
    return [log.model_dump(mode="json") for log in result.logs]
