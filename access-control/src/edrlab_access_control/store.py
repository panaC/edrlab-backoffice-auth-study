from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, TypeVar


T = TypeVar("T")


class FileStateStore:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._default_state()
        with self.path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        state.setdefault("accounts", {})
        state.setdefault("serviceRoles", {})
        return state

    def save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with tmp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, self.path)

    def transact(self, callback: Callable[[dict[str, Any]], T]) -> T:
        with self._lock:
            state = self.load()
            result = callback(state)
            self.save(state)
            return result

    def _default_state(self) -> dict[str, Any]:
        return {"accounts": {}, "serviceRoles": {}}

