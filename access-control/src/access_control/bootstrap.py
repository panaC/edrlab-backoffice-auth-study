from __future__ import annotations

import json

from .audit import AuditWriter
from .config import audit_path, bootstrap_config
from .service import AccessControlService
from .store import state_store_from_env


def main() -> None:
    service = AccessControlService(state_store_from_env(), AuditWriter(audit_path()))
    result = service.bootstrap_first_super_admin(**bootstrap_config())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
