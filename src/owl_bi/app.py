from __future__ import annotations

import sqlalchemy as sa
from fastapi import FastAPI

from owl_bi.datasets.api import router as datasets_router
from owl_bi.datasets.registry import DatasetRegistry
from owl_bi.datasets.service import DatasetQueryService, EngineFactory


def _unconfigured_engine_factory(dataset_id: str) -> sa.Engine:
    raise RuntimeError(
        f"no engine_factory configured for dataset {dataset_id!r} — pass one "
        "to create_app() that resolves a dataset id to a SQLAlchemy engine "
        "for a real data source. See examples/toy_dashboard/server.py."
    )


def create_app(
    registry: DatasetRegistry | None = None,
    engine_factory: EngineFactory | None = None,
) -> FastAPI:
    """Build the Owl BI core FastAPI app.

    With no arguments this returns a working app with an *empty* dataset
    registry — it starts fine, but every `/internal/datasets/*/query` call
    404s until datasets are registered. That's intentional: there's no
    admin API or persistence for dataset configs yet (tracked in
    docs/architecture.md §8), so registration is code-level for now.
    """
    app = FastAPI(title="Owl BI", version="0.1.0")
    app.state.dataset_service = DatasetQueryService(
        registry or DatasetRegistry(),
        engine_factory or _unconfigured_engine_factory,
    )
    app.include_router(datasets_router)
    return app


app = create_app()
