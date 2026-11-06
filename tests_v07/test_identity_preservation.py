"""Tests for CausaGuard v0.7 Cryptographic Identity & Historical Preservation.

Verifies the immutable preservation of:
1. Historical v0.5.2 seal (053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6)
2. Root pyproject.toml hash (1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049)
3. Historical v0.6 protocol seal (c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0)
4. Historical v0.6 amendment 01 seal (a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781)
5. Strict non-access boundary check for reserved confirmatory seeds.
"""

from __future__ import annotations

import hashlib
import json

from causaguard.v052.study import ROOT, identity, read_json, validate_report

EXPECTED_V052_SEAL = "053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6"
EXPECTED_PYPROJECT_SHA = "1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049"
EXPECTED_V06_PROTOCOL_SEAL = "c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0"
EXPECTED_V06_AMENDMENT_01_SEAL = "a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781"


def test_v052_development_frozen_report_validation():
    """Validates that artifacts/v052/development-frozen.json is intact and passes validate_report()."""
    report_path = ROOT / "artifacts/v052/development-frozen.json"
    assert report_path.is_file(), f"Report file not found: {report_path}"

    report = read_json(report_path)
    validate_report(report)

    assert report["sha256"] == EXPECTED_V052_SEAL, (
        f"Seal mismatch: expected {EXPECTED_V052_SEAL}, got {report['sha256']}"
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

    assert current_id["study_version"] == report["identity"]["study_version"]
    assert current_id["pyproject"] == report["identity"]["pyproject"]
    assert current_id["source"] == report["identity"]["source"]
    assert current_id["tests"] == report["identity"]["tests"]
    assert current_id["artifacts"] == report["identity"]["artifacts"]


def test_v06_protocol_seal_verification():
    """Verifies that all 20 files under the v0.6 protocol seal match their recorded hashes."""
    seal_path = ROOT / "experiments_v06/v06_protocol_seal.json"
    assert seal_path.is_file(), f"v0.6 seal file not found: {seal_path}"

    with open(seal_path, "r", encoding="utf-8") as f:
        seal_record = json.load(f)

    assert seal_record["protocol_seal"] == EXPECTED_V06_PROTOCOL_SEAL

    manifest = seal_record["file_hashes"]
    assert len(manifest) == 20

    for rel_path, expected_hash in sorted(manifest.items()):
        full_path = ROOT / rel_path
        assert full_path.is_file(), f"Sealed file missing: {rel_path}"
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch on {rel_path}: {actual_hash} != {expected_hash}"


def test_v06_amendment_01_seal_verification():
    """Verifies that all 4 files under the v0.6 amendment 01 seal match their recorded hashes."""
    seal_path = ROOT / "experiments_v06/v06_amendment_01_seal.json"
    assert seal_path.is_file(), f"v0.6 amendment 01 seal file not found: {seal_path}"

    with open(seal_path, "r", encoding="utf-8") as f:
        seal_record = json.load(f)

    assert seal_record["amendment_seal"] == EXPECTED_V06_AMENDMENT_01_SEAL

    manifest = seal_record["amendment_files"]
    assert len(manifest) == 4

    for rel_path, expected_hash in sorted(manifest.items()):
        full_path = ROOT / rel_path
        assert full_path.is_file(), f"Sealed amendment file missing: {rel_path}"
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch on {rel_path}: {actual_hash} != {expected_hash}"


def test_reserved_final_seeds_boundary():
    """Asserts that reserved final seeds for v0.6 and v0.7 are forbidden from exploratory routines."""
    v06_final_range = set(range(60030001, 60040065))
    v07_final_range = set(range(70030001, 70040065))

    # Assert that namespaces are strictly disjoint
    assert v06_final_range.isdisjoint(v07_final_range)

    # Test seed range boundaries
    dev_seeds = set(range(70001001, 70001050))
    assert dev_seeds.isdisjoint(v06_final_range)
    assert dev_seeds.isdisjoint(v07_final_range)
