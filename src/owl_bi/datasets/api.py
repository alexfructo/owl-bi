# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from owl_bi.datasets.exceptions import DatasetNotFound, FilterNotAllowed
from owl_bi.datasets.service import DatasetQueryService

router = APIRouter(prefix="/internal/datasets", tags=["datasets"])


class QueryRequest(BaseModel):
    filters: dict[str, str] = Field(default_factory=dict)
    limit: int | None = None


class QueryResponse(BaseModel):
    rows: list[dict]


def get_dataset_service(request: Request) -> DatasetQueryService:
    return request.app.state.dataset_service


def verify_internal_token(authorization: str | None = Header(default=None)) -> None:
    """Shared-secret bearer token between the dashboard SDK and this API.

    This implements the mechanism proposed (but not yet built) in
    docs/architecture.md §8 — a single token via env var, not per-dataset
    or per-dashboard credentials. That's a known limitation: any caller
    with the token can query any registered dataset, subject only to that
    dataset's filter whitelist. Fine for the walking-skeleton stage where
    the caller is a trusted subprocess on the same host; revisit before
    this crosses a real trust boundary (e.g. multi-tenant hosting).
    """
    expected = os.environ.get("OWL_BI_INTERNAL_TOKEN")
    if not expected:
        raise HTTPException(status_code=500, detail="OWL_BI_INTERNAL_TOKEN is not configured")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="missing or invalid internal token")


@router.post(
    "/{dataset_id}/query",
    response_model=QueryResponse,
    dependencies=[Depends(verify_internal_token)],
)
def query_dataset(
    dataset_id: str,
    body: QueryRequest,
    service: DatasetQueryService = Depends(get_dataset_service),
) -> QueryResponse:
    try:
        rows = service.query(dataset_id, body.filters, body.limit)
    except DatasetNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FilterNotAllowed as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QueryResponse(rows=rows)
