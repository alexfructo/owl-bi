# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

from owl_bi.datasets.exceptions import DatasetNotFound
from owl_bi.datasets.models import DatasetConfig


class DatasetRegistry:
    """In-memory registry of dataset configs, keyed by dataset id.

    MVP only. There's no persistence or admin API yet — datasets are
    registered in code by whoever wires up the app (see
    examples/toy_dashboard/server.py). Swapping this for a DB-backed
    registry later shouldn't require touching DatasetQueryService, which
    only depends on this class's two methods.
    """

    def __init__(self) -> None:
        self._datasets: dict[str, DatasetConfig] = {}

    def register(self, config: DatasetConfig) -> None:
        self._datasets[config.id] = config

    def get(self, dataset_id: str) -> DatasetConfig:
        try:
            return self._datasets[dataset_id]
        except KeyError:
            raise DatasetNotFound(dataset_id) from None
