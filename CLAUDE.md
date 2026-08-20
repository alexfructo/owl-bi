# Owl BI — context for Claude Code sessions

**What this is:** an open source alternative to Power BI, much narrower in
scope — a platform to publish, control access to, and embed dashboards
built as Streamlit apps (Python + Streamlit + Plotly). Not a visual
report builder, not a data modeling layer. See [`README.md`](README.md)
for the pitch, [`docs/architecture.md`](docs/architecture.md) for the
full design notes (roles, dashboard lifecycle, RLS/dataset service,
open questions), and [`docs/product-scope.md`](docs/product-scope.md)
for the feature-by-feature comparison against Power BI (what's in scope,
deferred, or explicitly out — read this before assuming a Power BI
feature is or isn't wanted here).

**Status as of 2026-08-20:** brainstorm / early exploration. The repo has
no application code yet — only the pitch and architecture notes. Nothing
in the architecture doc is final; treat it as a running log, not a spec.

**Before starting implementation work**, read `docs/architecture.md` in
full — it has the reasoning behind key decisions (isolated subprocesses
over Docker, centralized RLS via a dataset service, WebSocket-aware
reverse proxy) and a list of things explicitly *not* decided yet (license,
dataset service API shape, subprocess auth mechanism). Don't re-litigate
those decisions without flagging that you're doing so; do surface the
open questions in §8 of that doc when they become relevant to the task at
hand.

**Scope discipline:** the biggest risk to this project is Power-BI-style
scope creep. No drag-and-drop builder, no DAX-equivalent modeling layer —
see §7 of the architecture doc before adding anything that smells like
either.
