# Toy dashboard (walking skeleton)

Proves the dataset service end-to-end against a real caller, before any
subprocess lifecycle manager or reverse proxy exists (see
[`docs/architecture.md`](../../docs/architecture.md) §9). Nothing here is
production shape — it's a manual stand-in for what the real dashboard
runtime will do later.

## Run it

From the repo root, with the `dev` extras installed (`pip install -e ".[dev]"`):

```bash
# 1. seed a small sqlite db with sales data across regions
python examples/toy_dashboard/seed_data.py

# 2. start the dataset service with the toy "sales" dataset registered
OWL_BI_INTERNAL_TOKEN=dev-token uvicorn examples.toy_dashboard.server:app --reload

# 3. in another terminal, start the dashboard
OWL_BI_INTERNAL_TOKEN=dev-token OWL_BI_API_URL=http://localhost:8000 \
    streamlit run examples/toy_dashboard/app.py
```

Open the dashboard and try `?region=north` vs `?region=south` in the URL —
each shows only that region's rows. That's RLS being enforced by the
dataset service, not by the dashboard trusting itself to filter correctly.

Edit `app.py` to request `filters={"product": "widget"}` instead and rerun
— the dataset service rejects it with a 400, because `product` isn't in
`DatasetConfig.allowed_filters` for this dataset (see `server.py`). That's
the whitelist from docs/architecture.md §4.3 doing its job.
