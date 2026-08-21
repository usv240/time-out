"""Thread-safe in-memory store mirroring the Xano encounter contract.

Xano remains the production target. This store makes the full synthetic workflow
executable and testable before the human-only Xano provisioning step is complete.
"""

from __future__ import annotations

from copy import deepcopy
from threading import RLock

from .models import EncounterRecord


class EncounterRepository:
    def __init__(self) -> None:
        self._rows: dict[str, EncounterRecord] = {}
        self._lock = RLock()

    def reset(self) -> None:
        with self._lock:
            self._rows.clear()

    def save(self, record: EncounterRecord) -> EncounterRecord:
        with self._lock:
            self._rows[record.id] = deepcopy(record)
            return deepcopy(record)

    def get(self, encounter_id: str) -> EncounterRecord:
        with self._lock:
            if encounter_id not in self._rows:
                raise KeyError(encounter_id)
            return deepcopy(self._rows[encounter_id])

    def list(self) -> list[EncounterRecord]:
        with self._lock:
            return [deepcopy(row) for row in self._rows.values()]
