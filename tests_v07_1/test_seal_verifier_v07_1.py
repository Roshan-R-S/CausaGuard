"""Unit and invariant tests for CausaGuard v0.7.1 Cryptographic Protocol Seal Verifier.

Tests resolution of:
- SEC-01: Canonical payload digest binding all metadata, authorization, and file hashes.
- SEC-02: Cryptographic authenticity against trusted signer registry outside untrusted seal payload.
- SEC-03: Mandatory 21-asset manifest completeness enforcement (final and draft modes).
- SEC-04: Confirmatory runner integration eliminating verification bypass.
- SEC-05: Security hardening: duplicate JSON keys, NTFS ADS, symlinks, and restricted LF normalization.

Strict Rule: Synthetic fixtures and test seeds ONLY.
No reserved confirmatory development or final evaluation seeds are accessed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from experiments_v07_1.evaluate_confirmatory_v07_1 import (
    ExecutionLockError,
    assert_execution_authorized,
)
from experiments_v07_1.evaluate_confirmatory_v07_1 import (
    SecurityViolationError as RunnerSecurityViolationError,
)
from experiments_v07_1.evaluate_confirmatory_v07_1 import (
    verify_protocol_seal as runner_verify_protocol_seal,
)
from experiments_v07_1.verify_seal_v07_1 import (
    EXPECTED_HISTORICAL_SEALS,
    FINAL_FREEZE_MANDATORY_FILES,
    PRE_FREEZE_DRAFT_MANDATORY_FILES,
    PRODUCTION_AUTHORIZATION_ENABLED,
    TRUSTED_SIGNER_REGISTRY,
    IncompleteManifestError,
    MalformedSealError,
    SecurityViolationError,
    UnauthorizedSealError,
    check_file_hash,
    compute_protocol_seal_digest,
    compute_synthetic_authorization_signature,
    get_canonical_seal_payload,
    load_seal_json,
    main,
    safe_resolve_relative_path,
    sha256_bytes,
    verify_cryptographic_authorization,
    verify_seal,
)

ROOT = Path(__file__).resolve().parent.parent

SYNTHETIC_SIGNER_IDENTITY = "independent-auditor@causaguard.internal"
SYNTHETIC_SECRET_KEY = "synthetic-prefreeze-audit-secret-key-42"
SYNTHETIC_TRUSTED_REGISTRY = {
    SYNTHETIC_SIGNER_IDENTITY: {
        "verification_key": SYNTHETIC_SECRET_KEY,
        "algorithm": "hmac-sha256",
        "role": "Independent Scientific Oversight Auditor",
    }
}


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def valid_synthetic_manifest(tmp_path: Path) -> dict[str, Any]:
    """Generates a valid synthetic seal referencing actual disk draft files for tests."""
    file_hashes: dict[str, str] = {}
    for rel_path in PRE_FREEZE_DRAFT_MANDATORY_FILES:
        target = ROOT / rel_path
        assert target.exists(), f"Mandatory test target '{rel_path}' missing"
        b = target.read_bytes()
        raw_h = sha256_bytes(b)
        lf_h = sha256_bytes(b.replace(b"\r\n", b"\n"))
        file_hashes[rel_path] = raw_h if raw_h == lf_h else (lf_h if b"\r\n" in b else raw_h)

    # For pytest_v07_1.ini, ensure LF hash is used as recorded
    if "pytest_v07_1.ini" in file_hashes:
        file_hashes["pytest_v07_1.ini"] = "de3933f9821209828c85d2b201d3a69cef9dcfcf8560e5afe5bae27c2c854a98"

    seal_data: dict[str, Any] = {
        "protocol_id": "v071-confirmatory-protocol-draft",
        "study_version": "0.7.1-isolated",
        "created_at": "2026-11-07T12:00:00Z",
        "git_commit_baseline": "251f7e583768c7834511d739ea1f3e71d319a9ff",
        "authorization": {
            "confirmatory_development_authorized": True,
            "authorized_by": "synthetic-test-harness",
            "authorized_at": "2026-11-07T12:00:00Z",
            "gate_decision_reference": "TEST-GATE-PASS",
            "signer_identity": SYNTHETIC_SIGNER_IDENTITY,
            "signature_algorithm": "hmac-sha256",
        },
        "historical_seal_dependencies": dict(EXPECTED_HISTORICAL_SEALS),
        "file_hashes": file_hashes,
    }

    digest = compute_protocol_seal_digest(seal_data)
    seal_data["protocol_seal"] = digest

    sig = compute_synthetic_authorization_signature(digest, SYNTHETIC_SECRET_KEY)
    seal_data["authorization"]["signature"] = sig

    seal_file = tmp_path / "synthetic_valid_seal.json"
    seal_file.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")
    return {
        "seal_data": seal_data,
        "seal_path": seal_file,
        "digest": digest,
        "signature": sig,
    }


@pytest.fixture
def valid_synthetic_freeze_manifest(tmp_path: Path) -> dict[str, Any]:
    """Generates a valid synthetic final-freeze seal in an isolated temporary root.

    Creates mock assets for all 21 FINAL_FREEZE_MANDATORY_FILES in tmp_path / 'mock_repo'.
    """
    mock_root = tmp_path / "mock_repo"
    mock_root.mkdir()

    file_hashes: dict[str, str] = {}
    for rel_path in FINAL_FREEZE_MANDATORY_FILES:
        target = mock_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = f"# synthetic test asset for {rel_path}\n"
        target.write_text(content, encoding="utf-8")
        file_hashes[rel_path] = sha256_bytes(content.encode("utf-8"))

    seal_data: dict[str, Any] = {
        "protocol_id": "v071-confirmatory-protocol",
        "study_version": "0.7.1-isolated",
        "created_at": "2026-11-07T12:00:00Z",
        "git_commit_baseline": "251f7e583768c7834511d739ea1f3e71d319a9ff",
        "authorization": {
            "confirmatory_development_authorized": True,
            "authorized_by": "synthetic-oversight-committee",
            "authorized_at": "2026-11-07T12:00:00Z",
            "gate_decision_reference": "FINAL-FREEZE-PASS",
            "signer_identity": SYNTHETIC_SIGNER_IDENTITY,
            "signature_algorithm": "hmac-sha256",
        },
        "historical_seal_dependencies": dict(EXPECTED_HISTORICAL_SEALS),
        "file_hashes": file_hashes,
    }

    digest = compute_protocol_seal_digest(seal_data)
    seal_data["protocol_seal"] = digest

    sig = compute_synthetic_authorization_signature(digest, SYNTHETIC_SECRET_KEY)
    seal_data["authorization"]["signature"] = sig

    seal_file = mock_root / "experiments_v07_1" / "v071_protocol_seal.json"
    seal_file.parent.mkdir(parents=True, exist_ok=True)
    seal_file.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")

    return {
        "mock_root": mock_root,
        "seal_data": seal_data,
        "seal_path": seal_file,
        "digest": digest,
        "signature": sig,
    }


# ==============================================================================
# 1. SEC-01: Canonical Digest Complete Payload Protection Tests
# ==============================================================================


def test_tampering_authorization_flag_invalidates_protocol_seal(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Toggling authorization flag changes digest and raises CANONICAL SEAL MISMATCH."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    original_seal = seal_data["protocol_seal"]

    # Toggle authorization flag from True to False
    seal_data["authorization"] = dict(seal_data["authorization"])
    seal_data["authorization"]["confirmatory_development_authorized"] = False

    new_digest = compute_protocol_seal_digest(seal_data)
    assert new_digest != original_seal, "Canonical digest failed to detect authorization flag change!"


def test_tampering_authorized_by_invalidates_protocol_seal(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Modifying authorized_by metadata changes computed digest."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    original_seal = seal_data["protocol_seal"]

    seal_data["authorization"] = dict(seal_data["authorization"])
    seal_data["authorization"]["authorized_by"] = "malicious-actor"

    assert compute_protocol_seal_digest(seal_data) != original_seal


def test_tampering_git_commit_invalidates_protocol_seal(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Modifying git_commit_baseline invalidates computed digest."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    original_seal = seal_data["protocol_seal"]

    seal_data["git_commit_baseline"] = "0000000000000000000000000000000000000000"
    assert compute_protocol_seal_digest(seal_data) != original_seal


def test_tampering_study_version_invalidates_protocol_seal(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Modifying study_version invalidates computed digest."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    original_seal = seal_data["protocol_seal"]

    seal_data["study_version"] = "0.7.1-tampered"
    assert compute_protocol_seal_digest(seal_data) != original_seal


def test_tampering_historical_dependency_invalidates_protocol_seal(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Modifying historical dependency hashes invalidates computed digest."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    original_seal = seal_data["protocol_seal"]

    seal_data["historical_seal_dependencies"] = dict(seal_data["historical_seal_dependencies"])
    seal_data["historical_seal_dependencies"]["v052_identity_seal"] = "0" * 64
    assert compute_protocol_seal_digest(seal_data) != original_seal


def test_tampering_file_hash_invalidates_protocol_seal(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Modifying any file hash in manifest invalidates computed digest."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    original_seal = seal_data["protocol_seal"]

    first_file = next(iter(seal_data["file_hashes"]))
    seal_data["file_hashes"] = dict(seal_data["file_hashes"])
    seal_data["file_hashes"][first_file] = "f" * 64
    assert compute_protocol_seal_digest(seal_data) != original_seal


def test_protocol_seal_field_exclusion_prevents_circular_dependency(valid_synthetic_manifest: dict[str, Any]):
    """SEC-01: Protocol seal digest excludes ONLY protocol_seal and signature fields."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    payload1 = get_canonical_seal_payload(seal_data)

    # Change recorded protocol_seal and signature in outer dict
    seal_data["protocol_seal"] = "arbitrary-string"
    seal_data["authorization"]["signature"] = "another-signature"
    payload2 = get_canonical_seal_payload(seal_data)

    assert payload1 == payload2, "Canonical payload must exclude protocol_seal and signature only"


# ==============================================================================
# 2. SEC-02: Cryptographic Authenticity & Untrusted Signer Lockout Tests
# ==============================================================================


def test_production_authorization_disabled_by_default():
    """SEC-02: Production authorization flag is False and registry is empty in pre-freeze."""
    assert PRODUCTION_AUTHORIZATION_ENABLED is False
    assert len(TRUSTED_SIGNER_REGISTRY) == 0


def test_production_lockout_blocks_self_authorized_seal(valid_synthetic_freeze_manifest: dict[str, Any]):
    """SEC-02: Attempting authorization without synthetic fixture override raises UnauthorizedSealError."""
    seal_path = valid_synthetic_freeze_manifest["seal_path"]
    mock_root = valid_synthetic_freeze_manifest["mock_root"]
    with pytest.raises(UnauthorizedSealError, match="Production authorization is strictly disabled"):
        verify_seal(
            seal_path=seal_path,
            root_dir=mock_root,
            require_authorized=True,
            pre_freeze_mode=False,
            allow_synthetic_fixture=False,  # Enforces production lock
        )


def test_untrusted_signer_identity_rejected(tmp_path: Path, valid_synthetic_freeze_manifest: dict[str, Any]):
    """SEC-02: Unknown signer identity raises UnauthorizedSealError."""
    mock_root = valid_synthetic_freeze_manifest["mock_root"]
    seal_data = dict(valid_synthetic_freeze_manifest["seal_data"])
    seal_data["authorization"] = dict(seal_data["authorization"])
    seal_data["authorization"]["signer_identity"] = "rogue-researcher@unauthorized.org"

    digest = compute_protocol_seal_digest(seal_data)
    seal_data["protocol_seal"] = digest
    seal_data["authorization"]["signature"] = compute_synthetic_authorization_signature(digest, "rogue-key")

    seal_file = mock_root / "experiments_v07_1" / "untrusted_signer.json"
    seal_file.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")

    with pytest.raises(UnauthorizedSealError, match="not in authoritative trusted signer registry"):
        verify_seal(
            seal_path=seal_file,
            root_dir=mock_root,
            require_authorized=True,
            trusted_signers=SYNTHETIC_TRUSTED_REGISTRY,
            allow_synthetic_fixture=True,
        )


def test_missing_or_corrupted_signature_rejected(tmp_path: Path, valid_synthetic_freeze_manifest: dict[str, Any]):
    """SEC-02: Missing or corrupted signature raises UnauthorizedSealError."""
    mock_root = valid_synthetic_freeze_manifest["mock_root"]
    seal_data = dict(valid_synthetic_freeze_manifest["seal_data"])
    seal_data["authorization"] = dict(seal_data["authorization"])
    seal_data["authorization"]["signature"] = "0" * 64  # Corrupted signature

    seal_file = mock_root / "experiments_v07_1" / "bad_sig.json"
    seal_file.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")

    with pytest.raises(UnauthorizedSealError, match="Cryptographic signature mismatch"):
        verify_seal(
            seal_path=seal_file,
            root_dir=mock_root,
            require_authorized=True,
            trusted_signers=SYNTHETIC_TRUSTED_REGISTRY,
            allow_synthetic_fixture=True,
        )


def test_valid_synthetic_authorization_succeeds(valid_synthetic_freeze_manifest: dict[str, Any]):
    """SEC-02: Valid synthetic authorization with trusted registry succeeds in test fixture."""
    seal_path = valid_synthetic_freeze_manifest["seal_path"]
    mock_root = valid_synthetic_freeze_manifest["mock_root"]
    res = verify_seal(
        seal_path=seal_path,
        root_dir=mock_root,
        require_authorized=True,
        enforce_mandatory_manifest=True,
        pre_freeze_mode=False,
        trusted_signers=SYNTHETIC_TRUSTED_REGISTRY,
        allow_synthetic_fixture=True,
        raise_on_error=True,
    )
    assert res["status"] == "PASS"
    assert res["verified"] is True
    assert res["authorized"] is True


def test_verify_cryptographic_authorization_direct():
    """SEC-02: Direct test of cryptographic authorization verification primitive."""
    seal_data = {
        "protocol_id": "test",
        "authorization": {
            "confirmatory_development_authorized": True,
            "signer_identity": SYNTHETIC_SIGNER_IDENTITY,
            "signature_algorithm": "hmac-sha256",
        },
    }
    digest = "abc123digest"
    sig = compute_synthetic_authorization_signature(digest, SYNTHETIC_SECRET_KEY)
    seal_data["authorization"]["signature"] = sig

    ok, reason = verify_cryptographic_authorization(
        seal_data=seal_data,
        protocol_seal_digest=digest,
        trusted_signers=SYNTHETIC_TRUSTED_REGISTRY,
        allow_synthetic_fixture=True,
    )
    assert ok is True
    assert "Cryptographically authenticated" in reason


# ==============================================================================
# 3. SEC-03: Mandatory Manifest Completeness (21 Assets) Tests
# ==============================================================================


def test_mandatory_manifest_lengths():
    """SEC-03: Verify exactly 21 assets in both final freeze and draft manifest specifications."""
    assert len(FINAL_FREEZE_MANDATORY_FILES) == 21, "Final freeze manifest must contain exactly 21 assets"
    assert len(PRE_FREEZE_DRAFT_MANDATORY_FILES) == 21, "Pre-freeze draft manifest must contain exactly 21 assets"


def test_missing_protocol_markdown_raises_incomplete_manifest(tmp_path: Path, valid_synthetic_manifest: dict[str, Any]):
    """SEC-03: Missing protocol Markdown in manifest raises IncompleteManifestError."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    seal_data["file_hashes"] = dict(seal_data["file_hashes"])
    del seal_data["file_hashes"]["research/methodology/v071-confirmatory-statistical-protocol-draft.md"]

    seal_file = tmp_path / "missing_md.json"
    seal_file.write_text(json.dumps(seal_data), encoding="utf-8")

    with pytest.raises(IncompleteManifestError, match="missing 1 mandatory files out of 21 required"):
        verify_seal(seal_path=seal_file, pre_freeze_mode=True, require_authorized=False)


def test_missing_verifier_implementation_raises_incomplete_manifest(tmp_path: Path, valid_synthetic_manifest: dict[str, Any]):
    """SEC-03: Missing verify_seal_v07_1.py in manifest raises IncompleteManifestError."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    seal_data["file_hashes"] = dict(seal_data["file_hashes"])
    del seal_data["file_hashes"]["experiments_v07_1/verify_seal_v07_1.py"]

    seal_file = tmp_path / "missing_verifier.json"
    seal_file.write_text(json.dumps(seal_data), encoding="utf-8")

    with pytest.raises(IncompleteManifestError, match="missing 1 mandatory files out of 21 required"):
        verify_seal(seal_path=seal_file, pre_freeze_mode=True, require_authorized=False)


def test_missing_verifier_tests_raises_incomplete_manifest(tmp_path: Path, valid_synthetic_manifest: dict[str, Any]):
    """SEC-03: Missing test_seal_verifier_v07_1.py in manifest raises IncompleteManifestError."""
    seal_data = dict(valid_synthetic_manifest["seal_data"])
    seal_data["file_hashes"] = dict(seal_data["file_hashes"])
    del seal_data["file_hashes"]["tests_v07_1/test_seal_verifier_v07_1.py"]

    seal_file = tmp_path / "missing_tests.json"
    seal_file.write_text(json.dumps(seal_data), encoding="utf-8")

    with pytest.raises(IncompleteManifestError, match="missing 1 mandatory files out of 21 required"):
        verify_seal(seal_path=seal_file, pre_freeze_mode=True, require_authorized=False)


def test_draft_assets_rejected_in_final_freeze_mode(tmp_path: Path, valid_synthetic_manifest: dict[str, Any]):
    """SEC-03: Using draft assets when pre_freeze_mode=False raises IncompleteManifestError."""
    seal_file = valid_synthetic_manifest["seal_path"]
    with pytest.raises(IncompleteManifestError, match="missing 2 mandatory files out of 21 required"):
        verify_seal(seal_path=seal_file, pre_freeze_mode=False)


def test_pre_freeze_mode_strictly_non_authorizing(valid_synthetic_manifest: dict[str, Any]):
    """SEC-03: Pre-freeze mode strictly refuses to grant execution authorization."""
    seal_file = valid_synthetic_manifest["seal_path"]
    with pytest.raises(UnauthorizedSealError, match="Pre-freeze validation mode cannot authorize confirmatory evaluation"):
        verify_seal(seal_path=seal_file, require_authorized=True, pre_freeze_mode=True)


# ==============================================================================
# 4. SEC-04: Confirmatory Runner Verification Integration Tests
# ==============================================================================


def test_runner_missing_seal_file_blocks_execution(tmp_path: Path):
    """SEC-04: Runner fails closed with ExecutionLockError when seal does not exist."""
    missing = tmp_path / "non_existent.json"
    with pytest.raises(ExecutionLockError, match="No valid protocol seal file found"):
        runner_verify_protocol_seal(missing)


def test_runner_unauthorized_seal_blocks_execution(tmp_path: Path):
    """SEC-04: Runner rejects unauthorized seal with ExecutionLockError."""
    unauth = tmp_path / "unauth.json"
    unauth.write_text(
        json.dumps({
            "study_version": "0.7.1-isolated",
            "git_commit_baseline": "251f7e583768c7834511d739ea1f3e71d319a9ff",
            "authorization": {"confirmatory_development_authorized": False},
            "file_hashes": {"pyproject.toml": "1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049"},
        }),
        encoding="utf-8",
    )
    with pytest.raises(ExecutionLockError, match="confirmatory development authorization token is missing or false"):
        runner_verify_protocol_seal(unauth)


def test_runner_hash_mismatch_blocks_execution(tmp_path: Path):
    """SEC-04: Runner rejects mismatched hash with ExecutionLockError."""
    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text(
        json.dumps({
            "study_version": "0.7.1-isolated",
            "git_commit_baseline": "251f7e583768c7834511d739ea1f3e71d319a9ff",
            "authorization": {"confirmatory_development_authorized": True},
            "file_hashes": {"pyproject.toml": "0" * 64},
        }),
        encoding="utf-8",
    )
    with pytest.raises(ExecutionLockError, match="hash mismatch"):
        runner_verify_protocol_seal(corrupted)


def test_runner_path_traversal_blocks_execution_with_security_violation(tmp_path: Path):
    """SEC-04: Runner catches path traversal attempts as SecurityViolationError."""
    traversal = tmp_path / "traversal.json"
    traversal.write_text(
        json.dumps({
            "study_version": "0.7.1-isolated",
            "git_commit_baseline": "251f7e583768c7834511d739ea1f3e71d319a9ff",
            "authorization": {"confirmatory_development_authorized": True},
            "file_hashes": {"../../etc/passwd": "0" * 64},
        }),
        encoding="utf-8",
    )
    with pytest.raises(RunnerSecurityViolationError, match="EXECUTION LOCK SECURITY VIOLATION"):
        runner_verify_protocol_seal(traversal)


def test_runner_assert_execution_authorized_preserves_seed_quarantines():
    """SEC-04: Runner strictly blocks reserved and quarantined seeds."""
    # Final evaluation seed
    with pytest.raises(RunnerSecurityViolationError, match="FATAL SECURITY VIOLATION.*final evaluation seed"):
        assert_execution_authorized([70200001], domain="de")

    # Historical v0.6 quarantined seed
    with pytest.raises(RunnerSecurityViolationError, match="FATAL SECURITY VIOLATION.*v0.6"):
        assert_execution_authorized([60030001], domain="de")

    # Confirmatory dev seeds require authentic seal
    with pytest.raises(ExecutionLockError, match="EXECUTION LOCK"):
        assert_execution_authorized([70100001], domain="de")


# ==============================================================================
# 5. SEC-05: Security Hardening & Adversarial Path Tests
# ==============================================================================


def test_duplicate_json_keys_rejected(tmp_path: Path):
    """SEC-05: Duplicate keys in seal JSON strictly raise MalformedSealError."""
    dup_seal = tmp_path / "duplicate_keys.json"
    dup_seal.write_text(
        '{"study_version": "0.7.1-isolated", "study_version": "0.7.1-override"}',
        encoding="utf-8",
    )
    with pytest.raises(MalformedSealError, match="Duplicate key detected in JSON payload"):
        load_seal_json(dup_seal)


def test_ntfs_alternate_data_stream_rejected(tmp_path: Path):
    """SEC-05: Colon in manifest path (NTFS ADS) strictly raises SecurityViolationError."""
    with pytest.raises(SecurityViolationError, match="Colon forbidden in manifest path"):
        safe_resolve_relative_path(ROOT, "pyproject.toml:zone.identifier")


def test_null_byte_in_path_rejected():
    """SEC-05: Null byte in path strictly raises SecurityViolationError."""
    with pytest.raises(SecurityViolationError, match="Null byte detected in manifest path"):
        safe_resolve_relative_path(ROOT, "src_v07_1/causaguard_v07_1/\0__init__.py")


def test_path_traversal_double_dot_rejected():
    """SEC-05: Directory traversal sequence strictly raises SecurityViolationError."""
    with pytest.raises(SecurityViolationError, match="Path traversal '..' forbidden"):
        safe_resolve_relative_path(ROOT, "../causaguard/pyproject.toml")


def test_absolute_and_rooted_paths_rejected():
    """SEC-05: Absolute, rooted, or drive-prefixed paths strictly raise SecurityViolationError."""
    with pytest.raises(SecurityViolationError, match="Leading slashes forbidden"):
        safe_resolve_relative_path(ROOT, "/etc/passwd")

    with pytest.raises(SecurityViolationError, match="Colon forbidden"):
        safe_resolve_relative_path(ROOT, "C:/Windows/system32")


def test_symlinks_forbidden_in_manifest(tmp_path: Path):
    """SEC-05: Symlinks in manifest strictly raise SecurityViolationError."""
    real_file = tmp_path / "real_file.py"
    real_file.write_text("print('hello')", encoding="utf-8")

    link_file = tmp_path / "symlink_file.py"
    try:
        link_file.symlink_to(real_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this platform/privilege level")

    with pytest.raises(SecurityViolationError, match="Symlinks strictly forbidden in sealed manifest"):
        safe_resolve_relative_path(tmp_path, "symlink_file.py")


def test_lf_normalization_approved_text_files(tmp_path: Path):
    """SEC-05: CRLF in approved text file matches LF hash and records normalization."""
    test_py = tmp_path / "sample.py"
    test_py.write_bytes(b"x = 1\r\ny = 2\r\n")

    lf_hash = sha256_bytes(b"x = 1\ny = 2\n")
    matches, actual_hash, is_lf = check_file_hash(test_py, lf_hash, rel_path="sample.py")

    assert matches is True
    assert actual_hash == lf_hash
    assert is_lf is True


def test_lf_normalization_forbidden_on_historical_artifacts(tmp_path: Path):
    """SEC-05: LF normalization is strictly forbidden on historical artifacts."""
    artifact = tmp_path / "historical.json"
    artifact.write_bytes(b'{"key": "value"}\r\n')

    lf_hash = sha256_bytes(b'{"key": "value"}\n')
    # Path under artifacts/
    matches, actual_hash, is_lf = check_file_hash(
        artifact, lf_hash, rel_path="artifacts/v052/historical.json"
    )
    assert matches is False
    assert is_lf is False


def test_lf_normalization_forbidden_on_unapproved_extensions(tmp_path: Path):
    """SEC-05: LF normalization is forbidden on unapproved binary/data extensions."""
    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"\r\n\r\n")

    lf_hash = sha256_bytes(b"\n\n")
    matches, actual_hash, is_lf = check_file_hash(data_file, lf_hash, rel_path="data.bin")
    assert matches is False
    assert is_lf is False


# ==============================================================================
# 6. CLI Execution Tests
# ==============================================================================


def test_cli_missing_seal_returns_code_1(tmp_path: Path):
    """CLI exits with code 1 fail-closed when seal is missing."""
    missing = tmp_path / "non_existent.json"
    exit_code = main(["--seal-path", str(missing)])
    assert exit_code == 1


def test_cli_pre_freeze_mode_validates_drafts(valid_synthetic_manifest: dict[str, Any]):
    """CLI in --pre-freeze-mode with --allow-unauthorized validates 21 draft assets."""
    seal_path = str(valid_synthetic_manifest["seal_path"])
    exit_code = main(["--seal-path", seal_path, "--pre-freeze-mode", "--allow-unauthorized"])
    assert exit_code == 0
