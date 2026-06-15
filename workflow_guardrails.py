from __future__ import annotations

from dataclasses import dataclass

from workflow_schemas import WorkflowJSONDefinition, WorkflowJSONNode


@dataclass
class GuardrailViolation:
    rule_id: str
    severity: str
    node_id: str
    component: str
    message: str


def evaluate_workflow_guardrails(workflow: WorkflowJSONDefinition) -> list[GuardrailViolation]:
    """Return structural guardrail violations for the workflow graph."""

    violations: list[GuardrailViolation] = []
    node_map = {node.node_id: node for node in workflow.nodes}
    component_nodes = _component_nodes(workflow)

    c3_nodes = component_nodes.get("C3", [])
    c4_nodes = component_nodes.get("C4", [])
    c7_nodes = component_nodes.get("C7", [])
    c8_nodes = component_nodes.get("C8", [])
    c9_nodes = component_nodes.get("C9", [])

    for c4_node in c4_nodes:
        if not any(_has_path(workflow, c3.node_id, c4_node.node_id) for c3 in c3_nodes):
            violations.append(
                GuardrailViolation(
                    rule_id="GR-C4-REQUIRES-C3",
                    severity="error",
                    node_id=c4_node.node_id,
                    component="C4",
                    message="C4 Signature impossible sans C3 Contrat en amont.",
                )
            )

        if not any(_has_path(workflow, c4_node.node_id, c9.node_id) for c9 in c9_nodes):
            violations.append(
                GuardrailViolation(
                    rule_id="GR-C9-AFTER-C4",
                    severity="error",
                    node_id=c4_node.node_id,
                    component="C4",
                    message="C9 Comptabilité obligatoire après C4 Signature.",
                )
            )

    contractual_nodes = c3_nodes + c4_nodes
    for c8_node in c8_nodes:
        has_contract_after_ocr = any(
            _has_path(workflow, c8_node.node_id, contract_node.node_id)
            for contract_node in contractual_nodes
            if contract_node.node_id != c8_node.node_id
        )
        if has_contract_after_ocr:
            has_scoring_between = any(
                _has_path(workflow, c8_node.node_id, c7_node.node_id)
                and any(_has_path(workflow, c7_node.node_id, contract_node.node_id) for contract_node in contractual_nodes)
                for c7_node in c7_nodes
            )
            if not has_scoring_between:
                violations.append(
                    GuardrailViolation(
                        rule_id="GR-C8-REQUIRES-C7",
                        severity="error",
                        node_id=c8_node.node_id,
                        component="C8",
                        message="C8 OCR doit passer par C7 Scoring avant contractualisation.",
                    )
                )

    for component in ["C4", "C9"]:
        for node in component_nodes.get(component, []):
            if not node.requires_human_validation or not node.critical_action:
                violations.append(
                    GuardrailViolation(
                        rule_id=f"GR-{component}-HUMAN-VALIDATION",
                        severity="error",
                        node_id=node.node_id,
                        component=component,
                        message=f"{component} ne peut jamais être déclenché automatiquement sans validation humaine.",
                    )
                )

    missing_nodes = [
        edge
        for edge in workflow.edges
        if edge.source_node_id not in node_map or edge.target_node_id not in node_map
    ]
    for edge in missing_nodes:
        violations.append(
            GuardrailViolation(
                rule_id="GR-EDGE-NODE-MISSING",
                severity="error",
                node_id=edge.edge_id,
                component="-",
                message="Un edge référence un node inexistant.",
            )
        )

    return violations


def has_blocking_violations(violations: list[GuardrailViolation]) -> bool:
    return any(violation.severity == "error" for violation in violations)


def _component_nodes(workflow: WorkflowJSONDefinition) -> dict[str, list[WorkflowJSONNode]]:
    components: dict[str, list[WorkflowJSONNode]] = {}
    for node in workflow.nodes:
        component = str(node.component or node.config.get("component", "")).strip()
        if component:
            components.setdefault(component, []).append(node)
    return components


def _has_path(workflow: WorkflowJSONDefinition, source_node_id: str, target_node_id: str) -> bool:
    if source_node_id == target_node_id:
        return True

    adjacency: dict[str, list[str]] = {}
    for edge in workflow.edges:
        adjacency.setdefault(edge.source_node_id, []).append(edge.target_node_id)

    visited = set()
    stack = list(adjacency.get(source_node_id, []))
    while stack:
        node_id = stack.pop()
        if node_id == target_node_id:
            return True
        if node_id in visited:
            continue
        visited.add(node_id)
        stack.extend(adjacency.get(node_id, []))
    return False
