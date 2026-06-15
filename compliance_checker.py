from __future__ import annotations

import pandas as pd

from workflow_guardrails import GuardrailViolation, evaluate_workflow_guardrails, has_blocking_violations
from workflow_schemas import WorkflowJSONDefinition


def check_workflow_compliance(workflow: WorkflowJSONDefinition) -> dict[str, object]:
    violations = evaluate_workflow_guardrails(workflow)
    return {
        "is_compliant": not has_blocking_violations(violations),
        "blocking_errors": sum(1 for violation in violations if violation.severity == "error"),
        "warnings": sum(1 for violation in violations if violation.severity == "warning"),
        "violations": violations,
    }


def violations_to_dataframe(violations: list[GuardrailViolation]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Règle": violation.rule_id,
                "Sévérité": violation.severity,
                "Node": violation.node_id,
                "Composante": violation.component,
                "Message": violation.message,
            }
            for violation in violations
        ],
        columns=["Règle", "Sévérité", "Node", "Composante", "Message"],
    )
