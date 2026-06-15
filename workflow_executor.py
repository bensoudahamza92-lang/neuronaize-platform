from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from shared_models import ExecutionLog, WorkflowState
from workflow_guardrails import evaluate_workflow_guardrails, has_blocking_violations
from workflow_schemas import WorkflowJSONDefinition, WorkflowJSONEdge, WorkflowJSONNode


ComponentHandler = callable


@dataclass
class WorkflowExecutionResult:
    state: WorkflowState
    logs: list[ExecutionLog] = field(default_factory=list)


def default_component_registry() -> dict[str, object]:
    from recommender import execute_recommendation_component

    return {
        "C1": execute_recommendation_component,
        "C2": execute_passthrough_component,
        "C3": execute_passthrough_component,
        "C4": execute_passthrough_component,
        "C5": execute_passthrough_component,
        "C6": execute_passthrough_component,
        "C7": execute_passthrough_component,
        "C8": execute_passthrough_component,
        "C9": execute_passthrough_component,
        "C10": execute_condition_component,
    }


def execute_workflow_definition(
    workflow: WorkflowJSONDefinition,
    initial_state: WorkflowState | None = None,
    component_registry: dict[str, object] | None = None,
    max_steps: int = 100,
) -> WorkflowExecutionResult:
    registry = component_registry or default_component_registry()
    state = initial_state or WorkflowState(workflow_id=workflow.workflow_id)
    state.workflow_id = workflow.workflow_id
    state.status = "running"
    state.started_at = state.started_at or datetime.now()
    state.updated_at = datetime.now()
    logs: list[ExecutionLog] = []

    guardrail_violations = evaluate_workflow_guardrails(workflow)
    if guardrail_violations:
        state.variables["guardrail_violations"] = [
            {
                "rule_id": violation.rule_id,
                "severity": violation.severity,
                "node_id": violation.node_id,
                "component": violation.component,
                "message": violation.message,
            }
            for violation in guardrail_violations
        ]
        for violation in guardrail_violations:
            logs.append(
                _log(
                    workflow.workflow_id,
                    violation.node_id,
                    "error" if violation.severity == "error" else "warning",
                    violation.message,
                )
            )
        if has_blocking_violations(guardrail_violations):
            state.status = "failed"
            state.variables["execution_logs"] = [log.model_dump(mode="json") for log in logs]
            return WorkflowExecutionResult(state=state, logs=logs)

    node_map = {node.node_id: node for node in workflow.nodes}
    if not node_map:
        state.status = "completed"
        state.completed_at = datetime.now()
        logs.append(_log(workflow.workflow_id, None, "warning", "Workflow sans nodes."))
        return WorkflowExecutionResult(state=state, logs=logs)

    current_node_id = workflow.entry_node_id or workflow.nodes[0].node_id
    executed_steps = 0

    while current_node_id and executed_steps < max_steps:
        executed_steps += 1
        node = node_map.get(current_node_id)
        if node is None:
            state.status = "failed"
            logs.append(_log(workflow.workflow_id, current_node_id, "error", "Node introuvable."))
            break

        state.current_node_id = node.node_id
        if not node.enabled:
            logs.append(_log(workflow.workflow_id, node.node_id, "skipped", f"Node {node.name} désactivé."))
            current_node_id = _next_node_id(workflow, node.node_id, state)
            continue

        if _is_blocked_by_human_validation(workflow, node, state):
            state.status = "waiting_validation"
            logs.append(
                _log(
                    workflow.workflow_id,
                    node.node_id,
                    "warning",
                    f"Action critique bloquée avant validation humaine : {node.critical_action}.",
                )
            )
            break

        started = perf_counter()
        try:
            state = _execute_node(node, state, registry)
            duration_ms = int((perf_counter() - started) * 1000)
            logs.append(_log(workflow.workflow_id, node.node_id, "success", f"Node {node.name} exécuté.", duration_ms))
        except Exception as exc:
            duration_ms = int((perf_counter() - started) * 1000)
            logs.append(_log(workflow.workflow_id, node.node_id, "error", str(exc), duration_ms))
            if workflow.stop_on_error:
                state.status = "failed"
                break

        if node.node_type == "end":
            state.status = "completed"
            state.completed_at = datetime.now()
            break

        current_node_id = _next_node_id(workflow, node.node_id, state)
        state.updated_at = datetime.now()

    if executed_steps >= max_steps:
        state.status = "failed"
        logs.append(_log(workflow.workflow_id, state.current_node_id, "error", "Nombre maximum d'étapes atteint."))
    elif state.status == "running" and not current_node_id:
        state.status = "completed"
        state.completed_at = datetime.now()

    state.variables["execution_logs"] = [log.model_dump(mode="json") for log in logs]
    state.updated_at = datetime.now()
    return WorkflowExecutionResult(state=state, logs=logs)


def execute_passthrough_component(state: WorkflowState, node: WorkflowJSONNode | None = None) -> WorkflowState:
    variables = dict(state.variables or {})
    if node is not None:
        variables[f"{node.node_id}_executed"] = True
        variables[f"{node.node_id}_component"] = node.component
    state.variables = variables
    return state


def execute_condition_component(state: WorkflowState, node: WorkflowJSONNode | None = None) -> WorkflowState:
    """Execute C10 as a deterministic IF function."""

    variables = dict(state.variables or {})
    config = node.config if node is not None else {}
    variable = config.get("variable")
    operator = config.get("operator", "truthy")
    expected = config.get("value")
    actual = _resolve_value(variable, state) if variable else None
    result = evaluate_condition(actual, operator, expected)
    variables["C10_result"] = result
    if node is not None:
        variables[f"{node.node_id}_condition"] = result
    state.variables = variables
    return state


def evaluate_condition(actual: object, operator: str | None, expected: object = None) -> bool:
    op = (operator or "truthy").strip().lower()
    if op == "truthy":
        return bool(actual)
    if op == "falsy":
        return not bool(actual)
    if op in {"equals", "eq", "=="}:
        return actual == expected
    if op in {"not_equals", "ne", "!="}:
        return actual != expected
    if op in {"gt", ">"}:
        return _to_float(actual) > _to_float(expected)
    if op in {"gte", ">="}:
        return _to_float(actual) >= _to_float(expected)
    if op in {"lt", "<"}:
        return _to_float(actual) < _to_float(expected)
    if op in {"lte", "<="}:
        return _to_float(actual) <= _to_float(expected)
    if op == "contains":
        return str(expected) in str(actual)
    if op == "in":
        return actual in (expected or [])
    return False


def _execute_node(node: WorkflowJSONNode, state: WorkflowState, registry: dict[str, object]) -> WorkflowState:
    if node.node_type in {"start", "end"} and not node.component:
        return execute_passthrough_component(state, node)

    component = node.component or node.config.get("component")
    if not component:
        return execute_passthrough_component(state, node)

    handler = registry.get(str(component))
    if handler is None:
        raise ValueError(f"Composante non enregistrée : {component}")

    if component == "C1":
        return handler(state)  # type: ignore[misc]
    return handler(state, node)  # type: ignore[misc]


def _next_node_id(workflow: WorkflowJSONDefinition, source_node_id: str, state: WorkflowState) -> str | None:
    outgoing = [edge for edge in workflow.edges if edge.source_node_id == source_node_id]
    if not outgoing:
        return None

    default_target = None
    for edge in outgoing:
        if not edge.condition:
            default_target = edge.target_node_id
            continue
        if _edge_condition_matches(edge, state):
            return edge.target_node_id
    return default_target


def _edge_condition_matches(edge: WorkflowJSONEdge, state: WorkflowState) -> bool:
    condition = str(edge.condition or "").strip().lower()
    if condition in {"true", "always"}:
        return True
    if condition in {"false", "never"}:
        return False
    if condition in {"c10_true", "if_true"}:
        return bool(state.variables.get("C10_result"))
    if condition in {"c10_false", "if_false"}:
        return not bool(state.variables.get("C10_result"))

    config = edge.condition_config or {}
    if config:
        actual = _resolve_value(config.get("variable"), state)
        return evaluate_condition(actual, config.get("operator"), config.get("value"))
    return False


def _is_blocked_by_human_validation(
    workflow: WorkflowJSONDefinition,
    node: WorkflowJSONNode,
    state: WorkflowState,
) -> bool:
    if not workflow.require_human_validation and not node.requires_human_validation:
        return False
    if not node.critical_action and not node.requires_human_validation:
        return False
    return not bool(state.variables.get("human_validation_approved", False))


def _resolve_value(path: object, state: WorkflowState) -> object:
    if not path:
        return None
    text = str(path)
    if text.startswith("state."):
        current: object = state
        parts = text.split(".")[1:]
    else:
        current = state.variables
        parts = text.split(".")
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _log(
    workflow_id: str,
    node_id: str | None,
    status: str,
    message: str,
    duration_ms: int | None = None,
) -> ExecutionLog:
    return ExecutionLog(
        log_id=f"log-{uuid4().hex[:10]}",
        workflow_id=workflow_id,
        node_id=node_id,
        status=status,  # type: ignore[arg-type]
        message=message,
        duration_ms=duration_ms,
    )
