from __future__ import annotations

import os

import httpx


class OwlBIError(Exception):
    """Raised for any dataset query failure — auth, unknown dataset, unwhitelisted filter, etc."""


class OwlBIClient:
    """What a dashboard imports to fetch data, instead of talking to a database directly.

    Dashboards never see a connection string or write SQL — every call
    goes through the dataset service, which is where RLS is enforced (see
    docs/architecture.md §4.3). There is intentionally no way to pass raw
    SQL or an unwhitelisted filter column through this client; the server
    rejects those, this client just surfaces the rejection.

    `http_client` is exposed for tests — pass an `httpx.Client` wired to an
    ASGI transport to call the app in-process instead of over the network.
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 10.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("OWL_BI_API_URL", "http://localhost:8000")).rstrip("/")
        self.token = token or os.environ.get("OWL_BI_INTERNAL_TOKEN")
        if not self.token:
            raise OwlBIError(
                "no internal token: set OWL_BI_INTERNAL_TOKEN or pass token= explicitly"
            )
        self._client = http_client or httpx.Client(timeout=timeout)

    def query(
        self,
        dataset_id: str,
        filters: dict[str, str] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        response = self._client.post(
            f"{self.base_url}/internal/datasets/{dataset_id}/query",
            json={"filters": filters or {}, "limit": limit},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        if response.status_code >= 400:
            raise OwlBIError(
                f"dataset query for {dataset_id!r} failed ({response.status_code}): {response.text}"
            )
        return response.json()["rows"]
