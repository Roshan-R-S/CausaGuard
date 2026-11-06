"""Tests for CausaGuard v0.5.2 Cryptographic Identity & Historical Preservation."""

import hashlib
from pathlib import Path

from causaguard.v052.study import ROOT, file_hash, identity, read_json, validate_report

EXPECTED_SEAL = "053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6"
EXPECTED_PYPROJECT_SHA = "1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049"


def test_v052_development_frozen_report_validation():
    """Validates that artifacts/v052/development-frozen.json is intact and passes validate_report()."""
    report_path = ROOT / "artifacts/v052/development-frozen.json"
    assert report_path.is_file(), f"Report file not found: {report_path}"

    report = read_json(report_path)
    validate_report(report)

    assert report["sha256"] == EXPECTED_SEAL, (
        f"Seal mismatch: expected {EXPECTED_SEAL}, got {report['sha256']}"
    )


def test_pyproject_toml_preservation():
    """Asserts that root pyproject.toml is byte-identical to the preserved baseline."""
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.is_file()
    current_hash = hashlib.sha256(pyproject_path.read_bytes()).hexdigest()
    assert current_hash == EXPECTED_PYPROJECT_SHA, (
        f"pyproject.toml modified! Expected {EXPECTED_PYPROJECT_SHA}, got {current_hash}"
    )


def test_v052_identity_consistency():
    """Asserts that dynamic identity() computation matches historical frozen identity."""
    report_path = ROOT / "artifacts/v052/development-frozen.json"
    report = read_json(report_path)
    current_id = identity()

    # Compare sources, tests, pyproject, and artifacts
    assert current_id["study_version"] == report["identity"]["study_version"]
    assert current_id["pyproject"] == report["identity"]["pyproject"]
    assert current_id["source"] == report["identity"]["source"]
    assert current_id["tests"] == report["identity"]["tests"]
    assert current_id["artifacts"] == report["identity"]["artifacts"]

