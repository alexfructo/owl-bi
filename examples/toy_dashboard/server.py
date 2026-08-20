"""Wires up the Owl BI core app with one real dataset, for the walking-skeleton demo.

This is deliberately kept out of `owl_bi.app`, which stays generic — this
module is what a real deployment's setup code would eventually look like,
once dataset registration has a proper admin API (see
docs/architecture.md §8).

Run with:

    OWL_BI_INTERNAL_TOKEN=dev-token \
        uvicorn examples.toy_dashboard.server:app --reload
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa

from owl_bi.app import create_app
from owl_bi.datasets.models import DatasetConfig
from owl_bi.datasets.registry import DatasetRegistry

DB_PATH = Path(__file__).parent / "sales.db"

registry = DatasetRegistry()
registry.register(
    DatasetConfig(
        id="sales",
        table="sales",
        # "product" is deliberately NOT in this whitelist — a dashboard
        # can filter by region (the RLS dimension) but not by arbitrary
        # columns. Try adding a "product" filter from the dashboard and
        # watch the dataset service reject it.
        allowed_filters=frozenset({"region"}),
        max_rows=1_000,
    )
)

_engine = sa.create_engine(f"sqlite:///{DB_PATH}")


def _engine_factory(dataset_id: str) -> sa.Engine:
    return _engine


app = create_app(registry=registry, engine_factory=_engine_factory)
