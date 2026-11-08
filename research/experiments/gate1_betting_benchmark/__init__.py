"""Gate 1 Betting-Based Confidence Bounds Exploratory Benchmark.

Evaluates fixed-time betting upper confidence bounds and anytime-valid
confidence sequences against the corrected Maurer-Pontil empirical Bernstein
bound and cluster-level Clopper-Pearson comparator for Gate 1 operational risk qualification.

Reference:
Waudby-Smith & Ramdas (2024), "Estimating means of bounded random variables by betting",
Journal of the Royal Statistical Society: Series B, DOI: 10.1093/jrsssb/qkad009.

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
Confirmatory protocol draft, candidate controllers, and production authorization remain untouched.
"""

from __future__ import annotations

PRE_FREEZE_NO_GO: bool = True
PRODUCTION_AUTHORIZATION_ENABLED: bool = False

__all__ = [
    "PRE_FREEZE_NO_GO",
    "PRODUCTION_AUTHORIZATION_ENABLED",
]

