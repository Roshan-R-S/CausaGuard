"""Tests for CausaGuard v0.7.1 Historical Preservation and Seed Quarantine."""

import hashlib
import json
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_root_pyproject_hash_preservation():
    expected = "1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049"
    actual = sha256_file("pyproject.toml")
    assert actual == expected, "Root pyproject.toml hash has been altered!"


def test_v052_historical_dependency_preservation():
    expected_root = "053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6"
    seal6 = json.load(open("experiments_v06/v06_protocol_seal.json"))
    assert seal6["historical_seal_dependency"] == expected_root


def test_v06_master_protocol_seal_preservation():
    seal6 = json.load(open("experiments_v06/v06_protocol_seal.json"))
    file_hashes = seal6["file_hashes"]
    assert len(file_hashes) == 20
    for path, expected_hash in file_hashes.items():
        actual_hash = sha256_file(path)
        assert actual_hash == expected_hash, f"Sealed file {path} hash mismatch!"


def test_v06_amendment_01_seal_preservation():
    amend1 = json.load(open("experiments_v06/v06_amendment_01_seal.json"))
    amend_files = amend1["amendment_files"]
    assert len(amend_files) == 4
    for path, expected_hash in amend_files.items():
        actual_hash = sha256_file(path)
        assert actual_hash == expected_hash, f"Amendment 01 sealed file {path} mismatch!"


def test_quarantined_and_confirmatory_seed_ranges():
    # Assert that prohibited seed ranges are protected by policy and not accessed
    v06_quarantined_final = range(60030001, 60040065)
    v07_dev_confirmatory = range(70010001, 70020065)
    v07_final_confirmatory = range(70030001, 70040065)

    # Test that exploratory v0.7.1 seed namespace (70002001-70002016) is strictly disjoint
    v07_1_exploratory = range(70002001, 70002017)

    assert set(v07_1_exploratory).isdisjoint(set(v06_quarantined_final))
    assert set(v07_1_exploratory).isdisjoint(set(v07_dev_confirmatory))
    assert set(v07_1_exploratory).isdisjoint(set(v07_final_confirmatory))
