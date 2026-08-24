"""Integrity-checked cache boundary for every external sponsor operation.

Callers provide a non-secret request descriptor and a zero-argument live call.
Online mode executes exactly once and freezes the response under `.cache/live`.
Offline mode only replays a matching response and never invokes the callable.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, TypeVar


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_ROOT = ROOT / ".cache" / "live"
T = TypeVar("T")


class OperationCacheError(RuntimeError):
    """Base error for external-operation cache failures."""


class OperationCacheMiss(OperationCacheError):
    """Raised when offline replay has no exact request match."""


class CacheIntegrityError(OperationCacheError):
    """Raised when cached bytes no longer match their frozen digest."""


@dataclass(frozen=True)
class CacheMetadata:
    schema_version: int
    vendor: str
    operation: str
    request_sha256: str
    response_sha256: str
    payload_kind: str
    payload_file: str
    captured_at: str
    synthetic_only: bool


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _safe_segment(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "-_" else "-" for character in value)
    return cleaned.strip("-") or "operation"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class OperationCache:
    def __init__(self, root: Path | None = None) -> None:
        configured = os.getenv("BEFORE_CACHE_ROOT")
        self.root = Path(configured) if configured else (root or DEFAULT_CACHE_ROOT)

    @staticmethod
    def request_sha256(descriptor: Any) -> str:
        # The descriptor is never persisted; only this digest is written. Callers
        # must describe synthetic inputs and must never include credentials.
        return hashlib.sha256(_canonical_json(descriptor)).hexdigest()

    def _paths(self, vendor: str, operation: str, request_sha256: str, suffix: str) -> tuple[Path, Path]:
        directory = self.root / _safe_segment(vendor.lower()) / _safe_segment(operation.lower())
        stem = request_sha256[:24]
        return directory / f"{stem}.metadata.json", directory / f"{stem}.response{suffix}"

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def _write(
        self,
        *,
        vendor: str,
        operation: str,
        request_sha256: str,
        payload: bytes,
        payload_kind: str,
        suffix: str,
    ) -> bytes:
        metadata_path, payload_path = self._paths(vendor, operation, request_sha256, suffix)
        metadata = CacheMetadata(
            schema_version=1,
            vendor=vendor,
            operation=operation,
            request_sha256=request_sha256,
            response_sha256=hashlib.sha256(payload).hexdigest(),
            payload_kind=payload_kind,
            payload_file=payload_path.name,
            captured_at=datetime.now(UTC).isoformat(),
            synthetic_only=True,
        )
        self._atomic_write(payload_path, payload)
        self._atomic_write(metadata_path, json.dumps(asdict(metadata), indent=2).encode("utf-8"))
        return payload

    def _read(self, *, vendor: str, operation: str, request_sha256: str, suffix: str) -> tuple[CacheMetadata, bytes]:
        metadata_path, expected_payload_path = self._paths(vendor, operation, request_sha256, suffix)
        if not metadata_path.exists():
            raise OperationCacheMiss(
                f"No cached {vendor} {operation} response matches request {request_sha256[:12]}."
            )
        try:
            metadata = CacheMetadata(**json.loads(metadata_path.read_text(encoding="utf-8")))
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CacheIntegrityError(f"Invalid cache metadata for {vendor} {operation}.") from exc
        payload_path = metadata_path.parent / metadata.payload_file
        if payload_path != expected_payload_path or not payload_path.exists():
            raise CacheIntegrityError(f"Cached payload is missing for {vendor} {operation}.")
        payload = payload_path.read_bytes()
        if metadata.request_sha256 != request_sha256:
            raise CacheIntegrityError(f"Cached request digest mismatch for {vendor} {operation}.")
        if hashlib.sha256(payload).hexdigest() != metadata.response_sha256:
            raise CacheIntegrityError(f"Cached response digest mismatch for {vendor} {operation}.")
        if not metadata.synthetic_only:
            raise CacheIntegrityError(f"Cache is not marked synthetic-only for {vendor} {operation}.")
        return metadata, payload

    def json(
        self,
        *,
        vendor: str,
        operation: str,
        request_descriptor: Any,
        offline: bool,
        live_call: Callable[[], T],
    ) -> T:
        request_sha256 = self.request_sha256(request_descriptor)
        if offline:
            metadata, payload = self._read(
                vendor=vendor,
                operation=operation,
                request_sha256=request_sha256,
                suffix=".json",
            )
            if metadata.payload_kind != "json":
                raise CacheIntegrityError(f"Cached payload type mismatch for {vendor} {operation}.")
            return json.loads(payload.decode("utf-8"))
        result = live_call()
        payload = _canonical_json(result)
        self._write(
            vendor=vendor,
            operation=operation,
            request_sha256=request_sha256,
            payload=payload,
            payload_kind="json",
            suffix=".json",
        )
        return result

    def bytes(
        self,
        *,
        vendor: str,
        operation: str,
        request_descriptor: Any,
        offline: bool,
        live_call: Callable[[], bytes],
    ) -> bytes:
        request_sha256 = self.request_sha256(request_descriptor)
        if offline:
            metadata, payload = self._read(
                vendor=vendor,
                operation=operation,
                request_sha256=request_sha256,
                suffix=".bin",
            )
            if metadata.payload_kind != "bytes":
                raise CacheIntegrityError(f"Cached payload type mismatch for {vendor} {operation}.")
            return payload
        result = live_call()
        if not isinstance(result, bytes):
            raise TypeError(f"{vendor} {operation} live call must return bytes.")
        return self._write(
            vendor=vendor,
            operation=operation,
            request_sha256=request_sha256,
            payload=result,
            payload_kind="bytes",
            suffix=".bin",
        )
