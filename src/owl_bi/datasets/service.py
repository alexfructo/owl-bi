# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

from typing import Callable

import sqlalchemy as sa

from owl_bi.datasets.exceptions import DatasetNotFound, FilterNotAllowed
from owl_bi.datasets.registry import DatasetRegistry

__all__ = ["DatasetNotFound", "DatasetQueryService", "FilterNotAllowed"]

EngineFactory = Callable[[str], sa.Engine]


class DatasetQueryService:
    """The one place RLS-filtered queries get built and run.

    This exists to close the trust-boundary gap described in
    docs/architecture.md §4.3: RLS used to live inside dashboard code,
    where a creator could skip it by accident or on purpose. Here, a
    dashboard never sees a connection string or writes SQL — it calls
    `query(dataset_id, filters)` over HTTP (see datasets/api.py), and this
    is the only code path that turns that into a database query. There is
    no second path a dashboard can take to reach the data unfiltered.

    Safety properties, deliberately narrow for the MVP:
    - Filters are equality-only, one whitelisted column at a time — no
      arbitrary SQL or operators from the caller. This sidesteps the SQL
      injection risk entirely for the value side, since values are always
      bound parameters.
    - The whitelist (`DatasetConfig.allowed_filters`) is defined by
      whoever registers the dataset, never by the caller or the embed
      token — an unlisted column is rejected, not silently dropped or
      silently applied.
    - `table` and column names come from server-side config, not request
      input, so interpolating them into SQL text is safe; only filter
      *values* flow through as bind parameters.
    - Row limits are clamped server-side (`DatasetConfig.max_rows`), so a
      caller can ask for fewer rows but never more.

    Not handled yet (tracked in docs/architecture.md §8): connection
    pooling reuse across calls, response caching by
    (dataset_id, filter hash), and per-workspace rate limiting. The
    `engine_factory` seam exists so those can be added without changing
    this class's contract.
    """

    def __init__(self, registry: DatasetRegistry, engine_factory: EngineFactory) -> None:
        self._registry = registry
        self._engine_factory = engine_factory

    def query(
        self,
        dataset_id: str,
        filters: dict[str, str] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        config = self._registry.get(dataset_id)  # raises DatasetNotFound

        filters = filters or {}
        unknown = sorted(set(filters) - config.allowed_filters)
        if unknown:
            raise FilterNotAllowed(unknown)

        effective_limit = min(limit, config.max_rows) if limit is not None else config.max_rows
        effective_limit = max(effective_limit, 0)

        # Column names below are whitelist-validated above, not request
        # input we're trusting blindly — that's what makes the f-string
        # safe. Values always go through `params`, never into the string.
        clauses = [f"{column} = :{column}" for column in filters]
        sql = f"SELECT * FROM {config.table}"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " LIMIT :__limit"

        params = {**filters, "__limit": effective_limit}
        engine = self._engine_factory(dataset_id)
        with engine.connect() as conn:
            result = conn.execute(sa.text(sql), params)
            rows = [dict(row) for row in result.mappings()]
        return rows
