# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatasetConfig:
    """Server-side definition of a dataset a dashboard is allowed to query.

    This is the whitelist the dataset service enforces RLS against — see
    docs/architecture.md §4.3. Nothing here is ever influenced by the
    dashboard or the embed token; it's defined once by whoever owns the
    dataset.

    `table` is trusted, server-controlled input (interpolated directly into
    SQL). `allowed_filters` bounds which columns a caller may filter on —
    any filter key outside this set is rejected before a query is ever
    built. Filter *values* are always passed as bound parameters, never
    interpolated, regardless of what they contain.
    """

    id: str
    table: str
    allowed_filters: frozenset[str] = field(default_factory=frozenset)
    max_rows: int = 5_000
