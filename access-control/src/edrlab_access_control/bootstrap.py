from __future__ import annotations

import json

from .audit import AuditWriter
from .config import audit_path, bootstrap_config, state_path
from .service import AccessControlService
from .store import FileStateStore


def main() -> None:
    service = AccessControlService(FileStateStore(state_path()), AuditWriter(audit_path()))
    result = service.bootstrap_first_super_admin(**bootstrap_config())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
