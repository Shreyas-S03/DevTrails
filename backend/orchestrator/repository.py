from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import OrchestratorSettings


class SupabaseRepository:
    def __init__(self, settings: OrchestratorSettings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError(
                "Missing SUPABASE_URL or SUPABASE_SECRET_KEY/SUPABASE_SERVICE_ROLE_KEY environment variables."
            )

        self.base_url = settings.supabase_url.rstrip("/")
        self.rest_base_url = f"{self.base_url}/rest/v1"
        self.api_key = settings.supabase_service_role_key
        self.timeout_seconds = 20

    def fetch_rider_by_id(self, rider_id: str) -> dict[str, Any] | None:
        params = {
            "select": "*",
            "rider_id": f"eq.{rider_id}",
            "limit": "1",
        }
        data = self._request(
            method="GET",
            path="/riders",
            params=params,
        )
        if isinstance(data, list) and data:
            return data[0]
        return None

    def insert_claim_decision(self, claim_row: dict[str, Any]) -> dict[str, Any]:
        data = self._request(
            method="POST",
            path="/claims",
            payload=claim_row,
            return_representation=True,
        )
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        return {}

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        return_representation: bool = False,
    ) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.rest_base_url}{path}{query}"

        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if return_representation:
            headers["Prefer"] = "return=representation"

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = Request(
            url=url,
            data=body,
            headers=headers,
            method=method.upper(),
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Supabase REST error {exc.code} on {method.upper()} {path}: {error_body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                f"Supabase REST network error on {method.upper()} {path}: {exc}"
            ) from exc
