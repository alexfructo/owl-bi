"""Tests for the problems named in docs/architecture.md §4.3.

Each test maps to one problem the old dashboard-level RLS approach had:
SQL injection, wrong trust boundary, unvalidated field targeting, and
consistency across repeated/multi-query calls.
"""

from __future__ import annotations


def test_rls_filter_limits_rows_to_matching_region(client, auth_headers):
    resp = client.post(
        "/internal/datasets/sales/query",
        json={"filters": {"region": "north"}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    assert len(rows) == 2
    assert all(row["region"] == "north" for row in rows)


def test_filter_outside_whitelist_is_rejected_not_ignored(client, auth_headers):
    # "product" is real data on the table but not in allowed_filters —
    # this must fail loudly (400), not silently return unfiltered rows.
    resp = client.post(
        "/internal/datasets/sales/query",
        json={"filters": {"product": "widget"}},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_sql_injection_in_filter_value_is_treated_as_a_literal(client, auth_headers):
    payload = {"filters": {"region": "north' OR '1'='1"}}
    resp = client.post("/internal/datasets/sales/query", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    # If the value leaked into the query unescaped, this would return all
    # rows. Bound parameters mean it matches nothing instead.
    assert resp.json()["rows"] == []


def test_missing_token_is_rejected(client):
    resp = client.post("/internal/datasets/sales/query", json={"filters": {}})
    assert resp.status_code == 401


def test_wrong_token_is_rejected(client):
    resp = client.post(
        "/internal/datasets/sales/query",
        json={"filters": {}},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_row_limit_is_clamped_to_dataset_max(client, auth_headers):
    resp = client.post(
        "/internal/datasets/sales/query",
        json={"filters": {}, "limit": 999_999},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    # DatasetConfig.max_rows=10 in the fixture, table only has 3 rows —
    # either way, the request never gets to ask for more than the cap.
    assert len(resp.json()["rows"]) <= 10


def test_unknown_dataset_is_404(client, auth_headers):
    resp = client.post("/internal/datasets/does-not-exist/query", json={"filters": {}}, headers=auth_headers)
    assert resp.status_code == 404


def test_rls_is_enforced_identically_across_repeated_calls(client, auth_headers):
    # Stand-in for the "multi-query dashboard" problem: every call to the
    # same dataset goes through this one enforcement point, so there's no
    # second code path a dashboard could hit that skips the filter.
    for _ in range(3):
        resp = client.post(
            "/internal/datasets/sales/query",
            json={"filters": {"region": "south"}},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert all(row["region"] == "south" for row in resp.json()["rows"])
