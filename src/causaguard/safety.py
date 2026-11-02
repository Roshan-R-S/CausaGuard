"""Non-learned authorization boundary, independent of predicted utility."""

from causaguard.domain import Scenario


def authorization_block(scenario: Scenario) -> str | None:
    # Identity is intentional: truthy strings or integers are not authorization.
    if scenario.confirmation_present is not True:
        return "hard policy: missing explicit user confirmation"
    return None
