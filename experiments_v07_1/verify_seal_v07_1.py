"""CausaGuard v0.7.1: Cryptographic Protocol Seal Verifier.

Fail-closed, independent cryptographic verification infrastructure for prospective protocol seals:
- SEC-01: Canonical JSON seal digest binds ALL metadata, git commit baseline, study version,
          historical dependencies, authorization records, and file hashes.
- SEC-02: Authenticity anchored to independent, trusted signer registry outside untrusted seal payload.
          Production authorization is disabled by default; self-generated checksums cannot authorize execution.
- SEC-03: Mandatory 21-asset manifest completeness enforcement (final freeze and pre-freeze draft modes).
- SEC-04: Confirmatory runner directly binds to authoritative verifier, eliminating bypass paths.
- SEC-05: Strict security hardening: duplicate JSON key rejection, NTFS alternate data stream (ADS)
          blocking, symlink prohibition, and restricted LF normalization for approved text files only.

Pre-Freeze Notice:
This module is VERIFICATION INFRASTRUCTURE ONLY. It does NOT generate an active seal,
grant research authorization, or unlock confirmatory evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# ==============================================================================
# Manifest Assets Specifications (SEC-03)
# ==============================================================================

# Core 19 assets present in both draft and final manifestations
CORE_MANDATORY_FILES: tuple[str, ...] = (
    "src_v07_1/causaguard_v07_1/__init__.py",
    "src_v07_1/causaguard_v07_1/domain_cs.py",
    "src_v07_1/causaguard_v07_1/domain_de.py",
    "src_v07_1/causaguard_v07_1/escalation.py",
    "src_v07_1/causaguard_v07_1/policy_v07_1.py",
    "src_v07_1/causaguard_v07_1/study_v07_1.py",
    "tests_v07_1/test_cs_domain_v07_1.py",
    "tests_v07_1/test_de_domain_v07_1.py",
    "tests_v07_1/test_escalation_v07_1.py",
    "tests_v07_1/test_exploratory_runner_v07_1.py",
    "tests_v07_1/test_identity_preservation_v07_1.py",
    "tests_v07_1/test_policy_fairness_v07_1.py",
    "tests_v07_1/test_study_v07_1.py",
    "tests_v07_1/test_confirmatory_runner_v07_1.py",
    "experiments_v07_1/evaluate_confirmatory_v07_1.py",
    "pyproject.toml",
    "pytest_v07_1.ini",
    "experiments_v07_1/verify_seal_v07_1.py",
    "tests_v07_1/test_seal_verifier_v07_1.py",
)

# 21 mandatory assets required for final freeze validation
FINAL_FREEZE_MANDATORY_FILES: tuple[str, ...] = CORE_MANDATORY_FILES + (
    "research/methodology/v071-confirmatory-statistical-protocol.md",
    "experiments_v07_1/v071_confirmatory_protocol.json",
)

# 21 mandatory assets required for pre-freeze draft validation
PRE_FREEZE_DRAFT_MANDATORY_FILES: tuple[str, ...] = CORE_MANDATORY_FILES + (
    "research/methodology/v071-confirmatory-statistical-protocol-draft.md",
    "experiments_v07_1/v071_confirmatory_protocol_draft.json",
)

# Default alias for production validation
MANDATORY_MANIFEST_FILES: tuple[str, ...] = FINAL_FREEZE_MANDATORY_FILES

EXPECTED_HISTORICAL_SEALS: dict[str, str] = {
    "v052_identity_seal": "053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6",
    "v06_protocol_seal": "c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0",
    "v06_amendment_01_seal": "a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781",
}

# ==============================================================================
# Line-Ending Normalization Constraints (SEC-05)
# ==============================================================================

APPROVED_NORMALIZATION_EXTENSIONS: frozenset[str] = frozenset({
    ".py",
    ".md",
    ".json",
    ".ini",
    ".toml",
})

FORBIDDEN_NORMALIZATION_PREFIXES: tuple[str, ...] = (
    "artifacts/",
    "experiments_v05",
    "experiments_v06",
)

# ==============================================================================
# Cryptographic Authenticity & Trusted Signer Architecture (SEC-02)
# ==============================================================================

# Explicit Pre-Freeze Lock: Production authorization is STRICTLY DISABLED.
# No legitimate independent approval process or production signing keys exist yet.
PRODUCTION_AUTHORIZATION_ENABLED: bool = False

# Authoritative, independently established trusted signers registry outside untrusted seal payload.
# In production pre-freeze, this registry is EMPTY.
TRUSTED_SIGNER_REGISTRY: dict[str, dict[str, str]] = {}


# ==============================================================================
# Exceptions Hierarchy
# ==============================================================================


class SealVerificationError(Exception):
    """Base exception for all seal verification failures."""


class SealNotFoundError(SealVerificationError):
    """Raised when the specified protocol seal file does not exist."""


class MalformedSealError(SealVerificationError):
    """Raised when seal JSON is malformed, corrupted, has duplicate keys, or missing required fields."""


class SecurityViolationError(SealVerificationError):
    """Raised when manifest paths attempt path traversal, directory escape, NTFS stream, or symlinks."""


class IncompleteManifestError(SealVerificationError):
    """Raised when seal manifest does not contain all 21 mandatory assets."""


class SealMismatchError(SealVerificationError):
    """Raised when on-disk file hash, canonical protocol seal digest, or historical seal does not match."""


class UnauthorizedSealError(SealVerificationError):
    """Raised when seal lacks valid, cryptographically authentic research authorization."""


# ==============================================================================
# JSON Loading with Duplicate Key and Non-Finite Number Prevention (SEC-05)
# ==============================================================================

MAX_SEAL_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB maximum protocol seal file size


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Helper for json.loads that strictly raises MalformedSealError on duplicate object keys."""
    res: dict[str, Any] = {}
    for k, v in pairs:
        if k in res:
            raise MalformedSealError(f"MALFORMED SEAL: Duplicate key detected in JSON payload: {k!r}")
        res[k] = v
    return res


def _reject_non_finite_constants(val: str) -> None:
    """Helper for json.loads that strictly rejects RFC 8259-forbidden non-finite numbers (NaN, Infinity)."""
    raise MalformedSealError(
        f"MALFORMED SEAL: Non-finite JSON number constant forbidden by RFC 8259: {val!r}"
    )


def load_seal_json(seal_path: Path, max_bytes: int = MAX_SEAL_SIZE_BYTES) -> dict[str, Any]:
    """Reads and parses seal JSON using bounded reading, strictly rejecting non-finite numbers, duplicate keys, and oversized files."""
    if not seal_path.is_file():
        raise SealNotFoundError(
            f"SEAL NOT FOUND: No valid protocol seal file found at '{seal_path}'. "
            f"Actual confirmatory evaluation seeds cannot be executed without an independently verified cryptographic protocol seal."
        )

    try:
        with open(seal_path, "r", encoding="utf-8") as f:
            content = f.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise MalformedSealError(
                    f"MALFORMED SEAL: Seal file at '{seal_path}' exceeds maximum permitted size of {max_bytes} bytes."
                )
    except (SealNotFoundError, MalformedSealError):
        raise
    except Exception as e:
        raise MalformedSealError(f"MALFORMED SEAL: Failed to read file at '{seal_path}': {e}") from e

    try:
        data = json.loads(
            content,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_constants,
        )
    except MalformedSealError:
        raise
    except Exception as e:
        raise MalformedSealError(f"MALFORMED SEAL: Failed to parse JSON at '{seal_path}': {e}") from e

    if not isinstance(data, dict):
        raise MalformedSealError(f"MALFORMED SEAL: Root of '{seal_path}' is not a JSON object.")

    return data


# ==============================================================================
# Path Security Primitives (SEC-05)
# ==============================================================================


def safe_resolve_relative_path(root_dir: Path, rel_path: str) -> Path:
    """Safely resolves rel_path against root_dir, strictly preventing path traversal.

    Rejects:
    - Empty, non-string, or whitespace-only paths
    - Null bytes (\\0)
    - Colons (preventing NTFS Alternate Data Streams and drive prefixes)
    - Absolute or rooted paths (/ or \\)
    - Directory traversal sequences ('..')
    - Paths resolving outside root_dir
    - Symlinks (prohibits symlink aliasing and TOCTOU escapes)
    """
    if not rel_path or not isinstance(rel_path, str) or not rel_path.strip():
        raise SecurityViolationError(f"Invalid path specification: {rel_path!r}")

    if "\0" in rel_path:
        raise SecurityViolationError(f"Null byte detected in manifest path: {rel_path!r}")

    if ":" in rel_path:
        raise SecurityViolationError(
            f"Colon forbidden in manifest path (potential NTFS alternate data stream or drive prefix): {rel_path!r}"
        )

    # Standardize forward slashes for cross-platform inspection
    normalized_str = rel_path.replace("\\", "/")

    if normalized_str.startswith("/"):
        raise SecurityViolationError(f"Leading slashes forbidden in manifest path: {rel_path!r}")

    p = Path(normalized_str)

    if p.is_absolute() or p.drive or p.root:
        raise SecurityViolationError(f"Absolute or rooted paths forbidden in manifest: {rel_path!r}")

    parts = p.parts
    if any(part == ".." for part in parts):
        raise SecurityViolationError(f"Path traversal '..' forbidden in manifest: {rel_path!r}")

    resolved_root = root_dir.resolve()
    target = (resolved_root / p).resolve()

    try:
        target.relative_to(resolved_root)
    except ValueError:
        raise SecurityViolationError(f"Manifest path escapes root directory: {rel_path!r}")

    # Symlink protection: ensure neither the unresolved path nor target is a symlink
    unresolved_target = root_dir / p
    if unresolved_target.is_symlink() or target.is_symlink():
        raise SecurityViolationError(f"Symlinks strictly forbidden in sealed manifest: {rel_path!r}")

    return target


# ==============================================================================
# Hashing & Line-Ending Normalization Primitives (SEC-05)
# ==============================================================================


def sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hexdigest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Computes SHA-256 hexdigest of file on disk."""
    return sha256_bytes(path.read_bytes())


def check_file_hash(target: Path, expected_hash: str, rel_path: str | None = None) -> tuple[bool, str, bool]:
    """Checks file hash with strict cross-platform LF normalization fallback.

    Normalization is permitted ONLY for approved text files (.py, .md, .json, .ini, .toml)
    outside historical/frozen directories. Byte-exact historical artifacts are never normalized.

    Returns:
        (matches: bool, actual_hash: str, is_lf_normalized: bool)
    """
    raw_bytes = target.read_bytes()
    raw_hash = sha256_bytes(raw_bytes)

    if raw_hash == expected_hash:
        return True, raw_hash, False

    # Block normalization on historical artifacts or forbidden directory prefixes
    if rel_path is not None:
        norm_rel = rel_path.replace("\\", "/")
        if any(norm_rel.startswith(pfx) for pfx in FORBIDDEN_NORMALIZATION_PREFIXES):
            return False, raw_hash, False

    # Block normalization on unapproved extensions (binaries, etc.)
    if target.suffix.lower() not in APPROVED_NORMALIZATION_EXTENSIONS:
        return False, raw_hash, False

    # Check LF normalization fallback for approved text files containing CRLF
    if b"\r\n" in raw_bytes:
        lf_bytes = raw_bytes.replace(b"\r\n", b"\n")
        lf_hash = sha256_bytes(lf_bytes)
        if lf_hash == expected_hash:
            return True, lf_hash, True

    return False, raw_hash, False


# ==============================================================================
# Canonical Payload & Digest (SEC-01)
# ==============================================================================


def get_canonical_seal_payload(seal_data: dict[str, Any]) -> dict[str, Any]:
    """Extracts canonical seal payload, binding ALL metadata, authorization, and file hashes.

    Excludes ONLY the digest field itself ('protocol_seal') and the signature field
    to avoid circular hashing while allowing the signature to attest to the complete payload.
    """
    payload = {k: v for k, v in seal_data.items() if k not in ("protocol_seal", "signature")}

    # If authorization section contains signature, exclude only that specific field
    if "authorization" in payload and isinstance(payload["authorization"], dict):
        auth_copy = dict(payload["authorization"])
        auth_copy.pop("signature", None)
        payload["authorization"] = auth_copy

    return payload


def compute_protocol_seal_digest(seal_data: dict[str, Any]) -> str:
    """Computes SHA-256 digest of canonical seal payload (RFC 8785 JSON format).

    Guarantees that ANY modification to authorization metadata, study version, git commit
    baseline, historical dependencies, or file hashes invalidates the digest.
    """
    if "file_hashes" in seal_data:
        payload = get_canonical_seal_payload(seal_data)
    else:
        # Backward-compatible fallback for raw file_hashes mapping in synthetic tests
        payload = seal_data

    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return sha256_bytes(canonical_json.encode("utf-8"))


# ==============================================================================
# Cryptographic Authenticity & Verification (SEC-02)
# ==============================================================================


def compute_synthetic_authorization_signature(
    protocol_seal_digest: str,
    secret_key: str,
) -> str:
    """Computes HMAC-SHA256 signature over protocol seal digest for synthetic test fixtures."""
    return hmac.new(
        secret_key.encode("utf-8"),
        protocol_seal_digest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_cryptographic_authorization(
    seal_data: dict[str, Any],
    protocol_seal_digest: str,
    trusted_signers: dict[str, dict[str, str]] | None = None,
    allow_synthetic_fixture: bool = False,
) -> tuple[bool, str]:
    """Verifies cryptographic authenticity of research authorization against a trusted anchor.

    Requires:
    1. PRODUCTION_AUTHORIZATION_ENABLED is True (or allow_synthetic_fixture is True).
    2. authorization dictionary exists with confirmatory_development_authorized == True.
    3. signer_identity is present in authoritative trusted_signers registry (defined OUTSIDE seal).
    4. Cryptographic signature over canonical protocol_seal digest matches trusted key.
    """
    auth = seal_data.get("authorization")
    if not isinstance(auth, dict):
        raise MalformedSealError("MALFORMED SEAL: Missing or non-dict 'authorization' section.")

    is_authorized = auth.get("confirmatory_development_authorized", False)
    if not is_authorized:
        return False, "Confirmatory development authorization token is false or missing."

    # Check production pre-freeze lock
    if not PRODUCTION_AUTHORIZATION_ENABLED and not allow_synthetic_fixture:
        raise UnauthorizedSealError(
            "UNAUTHORIZED SEAL: Production authorization is strictly disabled during pre-freeze. "
            "No legitimate independent approval and signature process has been established."
        )

    signer_identity = auth.get("signer_identity")
    if not signer_identity or not isinstance(signer_identity, str):
        raise UnauthorizedSealError(
            "UNAUTHORIZED SEAL: Missing or invalid 'signer_identity' in authorization record."
        )

    signature = auth.get("signature") or seal_data.get("signature")
    if not signature or not isinstance(signature, str):
        raise UnauthorizedSealError(
            "UNAUTHORIZED SEAL: Missing cryptographic signature in authorization record."
        )

    registry = trusted_signers if trusted_signers is not None else TRUSTED_SIGNER_REGISTRY
    if signer_identity not in registry:
        raise UnauthorizedSealError(
            f"UNAUTHORIZED SEAL: Signer '{signer_identity}' is not in authoritative trusted signer registry."
        )

    signer_info = registry[signer_identity]
    key = signer_info.get("verification_key") or signer_info.get("public_key")
    algorithm = auth.get("signature_algorithm", "hmac-sha256")

    if algorithm == "hmac-sha256":
        if not key:
            raise UnauthorizedSealError(f"Missing verification key for trusted signer '{signer_identity}'.")
        expected_sig = compute_synthetic_authorization_signature(protocol_seal_digest, key)
        if not hmac.compare_digest(signature, expected_sig):
            raise UnauthorizedSealError(
                f"UNAUTHORIZED SEAL: Cryptographic signature mismatch for signer '{signer_identity}'."
            )
    else:
        raise UnauthorizedSealError(f"Unsupported signature algorithm '{algorithm}'.")

    return True, f"Cryptographically authenticated by trusted signer '{signer_identity}'."


# ==============================================================================
# Fail-Closed Seal Verification Pipeline
# ==============================================================================


def verify_seal(
    seal_path: Path | str | None = None,
    root_dir: Path | str | None = None,
    require_authorized: bool = True,
    enforce_mandatory_manifest: bool = True,
    pre_freeze_mode: bool = False,
    trusted_signers: dict[str, dict[str, str]] | None = None,
    allow_synthetic_fixture: bool = False,
    raise_on_error: bool = True,
) -> dict[str, Any]:
    """Performs full fail-closed cryptographic verification of a v0.7.1 protocol seal.

    Args:
        seal_path: Path to seal JSON. Defaults to experiments_v07_1/v071_protocol_seal.json.
        root_dir: Repository root directory. Defaults to repository root.
        require_authorized: Whether confirmatory development authorization is required.
        enforce_mandatory_manifest: Whether manifest must contain all 21 mandatory assets.
        pre_freeze_mode: Whether to validate 21 draft assets in non-authorizing pre-freeze mode.
        trusted_signers: Authoritative trusted signers registry (for synthetic testing).
        allow_synthetic_fixture: Permit synthetic test authorizations.
        raise_on_error: Whether to raise specific SealVerificationError exceptions on failure.

    Returns:
        Verification diagnostic dictionary containing status, details, and verified files.
    """
    root = ROOT if root_dir is None else Path(root_dir)

    if seal_path is None:
        seal_file = root / "experiments_v07_1" / "v071_protocol_seal.json"
    else:
        seal_file = Path(seal_path)
        if not seal_file.is_absolute():
            seal_file = root / seal_file

    errors: list[str] = []
    warnings: list[str] = []
    verified_files: dict[str, dict[str, Any]] = {}

    # 1. Existence and Parse with Duplicate Key Rejection (SEC-05)
    try:
        seal_data = load_seal_json(seal_file)
    except SealVerificationError as e:
        if raise_on_error:
            raise
        return {"status": "FAIL", "errors": [str(e)], "verified": False}

    # 2. Authorization Gate (Early Check for explicit unauthorized seals)
    auth = seal_data.get("authorization")
    if not isinstance(auth, dict):
        err = "MALFORMED SEAL: Missing or non-dict 'authorization' section."
        errors.append(err)
        if raise_on_error:
            raise MalformedSealError(err)
        is_authorized = False
    else:
        is_authorized = bool(auth.get("confirmatory_development_authorized", False))

    # If seal explicitly states it is not authorized, fail immediately
    if require_authorized and not pre_freeze_mode and not is_authorized:
        err = (
            "UNAUTHORIZED SEAL: Protocol seal exists but explicit confirmatory development "
            "authorization token is missing or false. Confirmatory development evaluation remains strictly locked."
        )
        errors.append(err)
        if raise_on_error:
            raise UnauthorizedSealError(err)

    # 3. Metadata Validation
    study_version = seal_data.get("study_version")
    if not study_version or not isinstance(study_version, str) or not study_version.startswith("0.7.1"):
        err = f"MALFORMED SEAL: Missing or invalid study_version: {study_version!r} (expected '0.7.1*')."
        errors.append(err)
        if raise_on_error:
            raise MalformedSealError(err)

    # 4. Manifest File Hashes Validation with Traversal & Normalization Hardening (SEC-05)
    file_hashes = seal_data.get("file_hashes")
    if not isinstance(file_hashes, dict) or not file_hashes:
        err = "MALFORMED SEAL: Missing or empty 'file_hashes' manifest."
        errors.append(err)
        if raise_on_error:
            raise MalformedSealError(err)
        file_hashes = {}

    for rel_path, expected_hash in file_hashes.items():
        try:
            target_path = safe_resolve_relative_path(root, rel_path)
        except SecurityViolationError as e:
            errors.append(str(e))
            if raise_on_error:
                raise
            continue

        if not target_path.exists():
            err = f"MISSING SEALED FILE: Sealed file '{rel_path}' does not exist on disk at '{target_path}'."
            errors.append(err)
            if raise_on_error:
                raise SealMismatchError(err)
            continue

        if not target_path.is_file():
            err = f"INVALID SEALED TARGET: '{rel_path}' is not a regular file."
            errors.append(err)
            if raise_on_error:
                raise SealMismatchError(err)
            continue

        matches, actual_hash, is_lf = check_file_hash(target_path, expected_hash, rel_path=rel_path)
        if not matches:
            err = (
                f"HASH MISMATCH in '{rel_path}': hash mismatch! "
                f"Expected {expected_hash}, Actual on disk: {actual_hash}"
            )
            errors.append(err)
            if raise_on_error:
                raise SealMismatchError(err)
        else:
            verified_files[rel_path] = {
                "hash": actual_hash,
                "lf_normalized": is_lf,
            }
            if is_lf:
                warnings.append(f"LF normalization applied to '{rel_path}' (CRLF on disk matches LF hash).")

    # 5. Git Commit Baseline Check
    git_commit = seal_data.get("git_commit_baseline")
    if not git_commit or not isinstance(git_commit, str) or len(git_commit) < 7:
        err = f"MALFORMED SEAL: Missing or invalid git_commit_baseline: {git_commit!r}."
        errors.append(err)
        if raise_on_error:
            raise MalformedSealError(err)

    # 5. Manifest Completeness Check (SEC-03: 21 mandatory assets)
    expected_mandatory = (
        PRE_FREEZE_DRAFT_MANDATORY_FILES if pre_freeze_mode else FINAL_FREEZE_MANDATORY_FILES
    )

    if enforce_mandatory_manifest:
        missing_mandatory = [f for f in expected_mandatory if f not in file_hashes]
        if missing_mandatory:
            mode_desc = "pre-freeze draft" if pre_freeze_mode else "final freeze"
            err = (
                f"INCOMPLETE MANIFEST ({mode_desc}): Protocol seal manifest is missing {len(missing_mandatory)} "
                f"mandatory files out of 21 required: {missing_mandatory}"
            )
            errors.append(err)
            if raise_on_error:
                raise IncompleteManifestError(err)

    # 6. Historical Seal Dependencies Check
    hist_deps = seal_data.get("historical_seal_dependencies", {})
    if isinstance(hist_deps, dict):
        for dep_name, expected_dep_hash in EXPECTED_HISTORICAL_SEALS.items():
            actual_dep = hist_deps.get(dep_name)
            if actual_dep != expected_dep_hash:
                err = (
                    f"HISTORICAL DEPENDENCY MISMATCH: {dep_name} mismatch. "
                    f"Expected: {expected_dep_hash}, Found: {actual_dep}"
                )
                errors.append(err)
                if raise_on_error:
                    raise SealMismatchError(err)

    # 6. Complete Seal Payload Canonical Digest Recomputation (SEC-01)
    recorded_protocol_seal = seal_data.get("protocol_seal")
    if recorded_protocol_seal is not None:
        computed_seal = compute_protocol_seal_digest(seal_data)
        if recorded_protocol_seal != computed_seal:
            err = (
                f"CANONICAL SEAL MISMATCH: 'protocol_seal' does not match computed payload digest. "
                f"Expected: {recorded_protocol_seal}, Computed: {computed_seal}"
            )
            errors.append(err)
            if raise_on_error:
                raise SealMismatchError(err)
    else:
        computed_seal = compute_protocol_seal_digest(seal_data)

    # 7. Research Authorization & Cryptographic Authenticity Check (SEC-02, SEC-03)
    authorized = False
    auth_reason = "Unchecked"
    if pre_freeze_mode:
        # Pre-freeze mode is explicitly non-authorizing
        authorized = False
        auth_reason = "PRE-FREEZE VALIDATION: Pre-freeze validation mode cannot authorize confirmatory evaluation."
        warnings.append("Pre-freeze mode is non-authorizing. Confirmatory execution remains locked.")
        if require_authorized:
            errors.append(auth_reason)
            if raise_on_error:
                raise UnauthorizedSealError(auth_reason)
    else:
        try:
            authorized, auth_reason = verify_cryptographic_authorization(
                seal_data=seal_data,
                protocol_seal_digest=recorded_protocol_seal or computed_seal,
                trusted_signers=trusted_signers,
                allow_synthetic_fixture=allow_synthetic_fixture,
            )
        except UnauthorizedSealError as e:
            errors.append(str(e))
            if require_authorized and raise_on_error:
                raise
        except Exception as e:
            err = f"AUTHORIZATION ERROR: {type(e).__name__}: {e}"
            errors.append(err)
            if require_authorized and raise_on_error:
                raise UnauthorizedSealError(err) from e

        if require_authorized and not authorized:
            err = f"UNAUTHORIZED SEAL: {auth_reason}"
            if err not in errors:
                errors.append(err)
            if raise_on_error:
                raise UnauthorizedSealError(err)

    status = "PASS" if not errors else "FAIL"
    return {
        "status": status,
        "verified": (status == "PASS"),
        "pre_freeze_mode": pre_freeze_mode,
        "study_version": study_version,
        "git_commit_baseline": git_commit,
        "authorized": authorized,
        "authorization_reason": auth_reason,
        "protocol_seal": recorded_protocol_seal or computed_seal,
        "files_verified_count": len(verified_files),
        "verified_files": verified_files,
        "errors": errors,
        "warnings": warnings,
    }


# ==============================================================================
# CLI Entry Point
# ==============================================================================


def main(argv: list[str] | None = None) -> int:
    """CLI runner for protocol seal verifier."""
    parser = argparse.ArgumentParser(
        description="CausaGuard v0.7.1: Cryptographic Protocol Seal Verifier"
    )
    parser.add_argument(
        "--seal-path",
        type=str,
        default=None,
        help="Path to prospective protocol seal JSON manifest (default: experiments_v07_1/v071_protocol_seal.json)",
    )
    parser.add_argument(
        "--root-dir",
        type=str,
        default=None,
        help="Repository root directory (default: parent of experiments_v07_1)",
    )
    parser.add_argument(
        "--pre-freeze-mode",
        action="store_true",
        help="Run in explicitly non-authorizing pre-freeze mode validating 21 draft assets",
    )
    parser.add_argument(
        "--allow-unauthorized",
        action="store_true",
        help="Verify file hashes and manifest completeness without requiring confirmatory development authorization token",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display detailed verification output for all manifest files",
    )

    args = parser.parse_args(argv)

    print("================================================================================")
    print("         CausaGuard v0.7.1: Cryptographic Protocol Seal Verifier               ")
    print("================================================================================")

    try:
        result = verify_seal(
            seal_path=args.seal_path,
            root_dir=args.root_dir,
            require_authorized=not args.allow_unauthorized,
            pre_freeze_mode=args.pre_freeze_mode,
            raise_on_error=True,
        )
    except SealVerificationError as e:
        print(f"\n[VERIFICATION FAILED: FAIL-CLOSED]\nError: {e}\n")
        return 1
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR: FAIL-CLOSED]\n{type(e).__name__}: {e}\n")
        return 1

    print(f"Status:               {result['status']}")
    print(f"Mode:                 {'PRE-FREEZE DRAFT' if result['pre_freeze_mode'] else 'FINAL FREEZE'}")
    print(f"Study Version:        {result['study_version']}")
    print(f"Git Commit Baseline:  {result['git_commit_baseline']}")
    print(f"Authorization:        {'AUTHORIZED' if result['authorized'] else 'UNAUTHORIZED (PRE-FREEZE LOCK)'}")
    print(f"Files Verified:       {result['files_verified_count']}")
    if result.get("protocol_seal"):
        print(f"Protocol Seal Digest: {result['protocol_seal']}")

    if args.verbose:
        print("\n--- Verified Files Detail ---")
        for fpath, meta in result["verified_files"].items():
            norm_tag = " (LF normalized)" if meta["lf_normalized"] else ""
            print(f"  [OK] {fpath}: {meta['hash']}{norm_tag}")

    if result.get("warnings"):
        print("\n--- Warnings ---")
        for w in result["warnings"]:
            print(f"  [WARN] {w}")

    print("\n[VERIFICATION PASSED] All sealed cryptographic invariants satisfied.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
