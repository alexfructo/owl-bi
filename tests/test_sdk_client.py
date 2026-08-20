# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from owl_bi.sdk import OwlBIClient, OwlBIError

BASE_URL = "http://testserver"


@pytest.fixture
def sdk_client(app):
    # FastAPI's TestClient subclasses httpx.Client and bridges sync calls
    # into the ASGI app for us, so it's a drop-in for OwlBIClient's
    # http_client seam — no real network or event loop needed.
    return OwlBIClient(base_url=BASE_URL, token="test-token", http_client=TestClient(app, base_url=BASE_URL))


def test_sdk_query_returns_filtered_rows(sdk_client):
    rows = sdk_client.query("sales", filters={"region": "north"})
    assert len(rows) == 2
    assert all(row["region"] == "north" for row in rows)


def test_sdk_surfaces_rejected_filter_as_error(sdk_client):
    with pytest.raises(OwlBIError):
        sdk_client.query("sales", filters={"product": "widget"})


def test_sdk_requires_a_token(monkeypatch):
    monkeypatch.delenv("OWL_BI_INTERNAL_TOKEN", raising=False)
    with pytest.raises(OwlBIError):
        OwlBIClient(base_url=BASE_URL, token=None)
