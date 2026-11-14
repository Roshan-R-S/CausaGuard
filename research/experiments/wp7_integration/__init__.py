"""Work Package 7 — Engineering Integration Package.

Governing Document: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP7, p. 17).
Implementation: Optional existing local Qwen3 demonstration, additive CLI, docs and tests.
Gate: All historical tests remain passing.
Status: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from research.experiments.wp7_integration.demonstration import (
    IndependentAuthorizationGuardV07_1,
    MockAgentV07_1,
    WP7Demonstrator,
    add_wp7_commands,
    replay_wp7_demonstration,
    run_wp7_command,
    run_wp7_demonstration,
)

__all__ = [
    "IndependentAuthorizationGuardV07_1",
    "MockAgentV07_1",
    "WP7Demonstrator",
    "add_wp7_commands",
    "replay_wp7_demonstration",
    "run_wp7_command",
    "run_wp7_demonstration",
]
