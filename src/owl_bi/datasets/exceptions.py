from __future__ import annotations


class DatasetNotFound(Exception):
    """Raised when a dataset id doesn't exist in the registry."""

    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"dataset {dataset_id!r} not found")


class FilterNotAllowed(Exception):
    """Raised when a query requests a filter column outside the dataset's whitelist."""

    def __init__(self, columns: list[str]) -> None:
        self.columns = columns
        super().__init__(f"filters not allowed for this dataset: {columns}")
