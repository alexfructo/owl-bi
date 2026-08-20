# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from owl_bi.app import create_app
from owl_bi.datasets.models import DatasetConfig
from owl_bi.datasets.registry import DatasetRegistry

TOKEN = "test-token"


@pytest.fixture
def engine():
    # StaticPool keeps every connection from this engine on the same
    # underlying in-memory sqlite db, so seeded data survives across the
    # multiple `engine.connect()` calls the service makes per request.
    eng = sa.create_engine(
        "sqlite://",
        poolclass=sa.pool.StaticPool,
        connect_args={"check_same_thread": False},
    )
    with eng.begin() as conn:
        conn.execute(sa.text("CREATE TABLE sales (region TEXT, product TEXT, amount INTEGER)"))
        conn.execute(
            sa.text("INSERT INTO sales (region, product, amount) VALUES (:region, :product, :amount)"),
            [
                {"region": "north", "product": "widget", "amount": 100},
                {"region": "north", "product": "gadget", "amount": 50},
                {"region": "south", "product": "widget", "amount": 200},
            ],
        )
    return eng


@pytest.fixture
def app(engine, monkeypatch):
    monkeypatch.setenv("OWL_BI_INTERNAL_TOKEN", TOKEN)
    registry = DatasetRegistry()
    registry.register(
        DatasetConfig(id="sales", table="sales", allowed_filters=frozenset({"region"}), max_rows=10)
    )
    return create_app(registry=registry, engine_factory=lambda dataset_id: engine)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {TOKEN}"}
