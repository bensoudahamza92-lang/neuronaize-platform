from __future__ import annotations

import pandas as pd


def simulate_channel_send(channel: str, require_human_validation: bool, campaign_validated: bool) -> str:
    """Return a demo status without sending any real notification."""

    if require_human_validation and not campaign_validated:
        return "À valider"
    if str(channel).lower().startswith("appel"):
        return "Simulé - tâche conseiller"
    return f"Simulé - {channel}"


def simulate_notification_batch(
    report: pd.DataFrame,
    require_human_validation: bool = True,
    campaign_validated: bool = False,
) -> pd.DataFrame:
    """Attach simulated notification statuses to a campaign report."""

    if report is None or report.empty:
        return pd.DataFrame()

    simulated = report.copy()
    simulated["Statut envoi"] = simulated["Canal proposé"].map(
        lambda channel: simulate_channel_send(channel, require_human_validation, campaign_validated)
    )
    return simulated
