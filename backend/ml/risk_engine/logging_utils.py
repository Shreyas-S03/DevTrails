from __future__ import annotations

from datetime import datetime, timezone


def log_stage(message: str, enabled: bool = True) -> None:
    if not enabled:
        return
    timestamp_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{timestamp_utc} UTC] {message}", flush=True)
