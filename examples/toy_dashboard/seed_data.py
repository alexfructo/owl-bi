"""Creates a small sqlite database to back the toy "sales" dataset.

Run once before starting the server:

    python examples/toy_dashboard/seed_data.py
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa

DB_PATH = Path(__file__).parent / "sales.db"

ROWS = [
    {"region": "north", "product": "widget", "amount": 100},
    {"region": "north", "product": "gadget", "amount": 50},
    {"region": "south", "product": "widget", "amount": 200},
    {"region": "south", "product": "gizmo", "amount": 75},
    {"region": "east", "product": "widget", "amount": 30},
]


def main() -> None:
    engine = sa.create_engine(f"sqlite:///{DB_PATH}")
    with engine.begin() as conn:
        conn.execute(sa.text("DROP TABLE IF EXISTS sales"))
        conn.execute(
            sa.text(
                "CREATE TABLE sales (region TEXT NOT NULL, product TEXT NOT NULL, amount INTEGER NOT NULL)"
            )
        )
        conn.execute(
            sa.text("INSERT INTO sales (region, product, amount) VALUES (:region, :product, :amount)"),
            ROWS,
        )
    print(f"seeded {len(ROWS)} rows into {DB_PATH}")


if __name__ == "__main__":
    main()
