"""Gate 1 statistical-design resolution package for CausaGuard v0.7.2.

Provides comparative statistical machinery across Designs A, B, and C:
- Maurer-Pontil corrected empirical Bernstein bound (2009 Theorem 4)
- Direct fixed-horizon betting test (Waudby-Smith & Ramdas 2024, aGRAPA)
- Constant-betting e-value test (Theorem 1, AM-GM inequality)
- Permutation-averaged betting test
- Hoeffding distribution-free bound (1963)

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
Confirmatory protocol draft, candidate controllers, and production authorization remain untouched.
"""

from __future__ import annotations

PRE_FREEZE_NO_GO: bool = True
PRODUCTION_AUTHORIZATION_ENABLED: bool = False
SAFETY_THRESHOLD: float = 0.0500
ALPHA: float = 0.050

# Seed quarantine: Confirmatory ranges (70100001+, 70200001+, 60030001+) are strictly prohibited
BASE_EXPLORATORY_SEED: int = 83000001

