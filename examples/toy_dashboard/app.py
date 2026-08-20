# SPDX-License-Identifier: AGPL-3.0-or-later
"""Toy Streamlit dashboard — the walking skeleton.

This is what a dashboard is meant to look like: it never touches a
database, only the SDK. There's no subprocess lifecycle manager or reverse
proxy yet (that's still open, see docs/architecture.md §9), so this is run
directly with `streamlit run` — but the RLS path it exercises is real,
going through the actual dataset service over HTTP.

Run (after seed_data.py and the server from this same directory are up):

    OWL_BI_INTERNAL_TOKEN=dev-token OWL_BI_API_URL=http://localhost:8000 \
        streamlit run examples/toy_dashboard/app.py

Try changing the region below, or edit this file to request a "product"
filter and see the dataset service reject it — that's the whitelist in
DatasetConfig.allowed_filters doing its job.
"""

from __future__ import annotations

import streamlit as st

from owl_bi.sdk import OwlBIClient, OwlBIError

st.title("Toy Sales Dashboard")
st.caption("Owl BI walking skeleton — real SDK call to a real dataset service.")

# In the real platform, the embed/session layer would inject this from the
# viewer's token. Here we just take it from a query param to simulate an
# RLS-filtered embed: try ?region=south in the URL.
region = st.query_params.get("region", "north")
st.write(f"RLS filter applied: `region = {region!r}`")

try:
    client = OwlBIClient()
    rows = client.query("sales", filters={"region": region})
except OwlBIError as exc:
    st.error(f"Dataset query failed: {exc}")
else:
    st.dataframe(rows)
    st.caption(f"{len(rows)} row(s) — only region {region!r} is visible, by design.")
