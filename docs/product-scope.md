# Owl BI — Product Scope vs. Power BI

**Status:** first deliberate pass at product scope. Until this doc,
`docs/architecture.md` §7 only had two negative guardrails ("no visual
builder", "no DAX-equivalent modeling") — that's a perimeter, not a
product definition. Architecture decisions (subprocess isolation,
dataset service, embed) got made before anyone systematically asked
"which parts of Power BI does Owl BI actually cover?" This doc is that
pass. Like `architecture.md`, treat it as a running log, not a spec.

## Method

Power BI's feature set was pulled from current docs/community sources
(linked per section) and grouped into categories. Each item is marked:

- ✅ **In scope** — decided, may not be built yet
- 🕓 **Open / deferred** — considered, not committed either way
- ❌ **Out of scope** — decided against, with the reasoning

## Publishing & distribution

| Feature | Status | Notes |
|---|---|---|
| Workspaces (edit) | ✅ | Existing — see architecture.md §3 |
| **Apps** — published view, separate from the edit workspace | ✅ **new** | Decided this session. Power BI separates the workspace people edit in from the "app" consumers see, so an in-progress edit doesn't break production viewers. Owl BI didn't have this distinction. See "Decisions made this session" below — needs its own design pass before it's built. |
| Embedding via token, params as RLS filters | ✅ | Existing — core pitch |
| Row-level security | ✅ | Existing — core pitch, see architecture.md §4.3 |

## Access & collaboration

| Feature | Status | Notes |
|---|---|---|
| Role-based access (Admin/Editor/Viewer at workspace level) | ✅ | Existing, matches Power BI's Admin/Member/Contributor/Viewer split closely enough |
| Comments on reports | 🕓 | Not core to the publishing-infra pitch; revisit if requested |

## Data refresh & connectivity

| Feature | Status | Notes |
|---|---|---|
| Scheduled dataset refresh | N/A | Doesn't map 1:1 — Streamlit fetches on demand, so "refresh" is whatever cadence the dashboard's own code chooses. The dataset service's planned response cache (architecture.md §4.3) is the closest analog, and it's already ✅ in scope. |
| Dataflows (reusable prep pipelines) | ❌ | This *is* the data modeling layer — excluded by the existing §7 guardrail |
| On-premises data gateway | 🕓 | Only matters once a real data source sits behind a firewall the dataset service can't reach directly. Might not need a dedicated gateway concept at all — "wherever the dataset service is hosted" may already solve it. Revisit if it comes up for real. |

## Interactivity & report features

| Feature | Status | Notes |
|---|---|---|
| Bookmarks, drillthrough | ❌ | These are report-authoring features. In Owl BI a dashboard is Streamlit code, so navigation/interactivity is the dashboard author's job, not the platform's — consistent with "dashboards are Streamlit code" |
| Q&A / natural language query / Copilot | ❌ | Squarely inside the "no DAX-equivalent modeling / no BI magic" guardrail. Worth noting Power BI's own Q&A is being retired in favor of Copilot (Dec 2026) — not a feature worth chasing even on Power BI's own roadmap. |
| Mobile-optimized layout | 🕓 | Streamlit has some responsiveness already; platform's job is mostly "don't break it in the proxy," not a dedicated mobile feature |

## Alerts & delivery

| Feature | Status | Notes |
|---|---|---|
| Data alerts (threshold-based notifications) | 🕓 **logged as "maybe later"** | Decided this session: not building now, not closing the door. Would need a threshold-evaluation engine plus a way to read a live Streamlit app's state outside a browser session — real infra, not a small add-on. |
| Subscriptions (scheduled email snapshot) | 🕓 **logged as "maybe later"** | Same bucket as alerts — needs headless rendering of a live Streamlit app (e.g. via a browser automation tool) to produce a static snapshot. Nontrivial, not started. |

## Deployment & lifecycle

| Feature | Status | Notes |
|---|---|---|
| Deployment pipelines (promote a dashboard dev → test → prod) | ✅ **new, in-platform** | Decided this session: build this *inside* Owl BI, not left to git branches/PRs outside the platform. This is a real scope addition, not yet designed — see open questions below. |

## Governance & admin

| Feature | Status | Notes |
|---|---|---|
| Usage metrics (who viewed which dashboard, when) | ✅ **new** | Decided this session: instrument at the reverse proxy (architecture.md §4.2) as it's built — that's the one chokepoint all dashboard traffic already passes through, so it's cheap now and expensive to retrofit later. |
| Audit log (workspace created, permissions changed, dataset registered, etc.) | ✅ **new** | Same reasoning — log at the FastAPI core as actions happen, not bolted on after the fact. |
| Tenant-wide admin settings/portal | 🕓 | Deferred until there's more than a couple of settings to actually administer |
| Capacity management (Premium-style compute tiers) | ❌ | Doesn't apply to a self-hosted open source model — whoever runs Owl BI owns the hardware. Per-dashboard resource limits (cgroups/ulimit, architecture.md §4.1) already cover "don't let one dashboard take down the host"; there's no capacity *product* to build on top of that. |

## AI features

| Feature | Status | Notes |
|---|---|---|
| Copilot / AI-generated insights | ❌ | Inside the "no BI magic" guardrail. Also not where the free-form-Python pitch has an edge — a dashboard author can already write whatever Python they need. |

## Licensing/capacity tiers

Power BI's Pro/Premium/Fabric-capacity tiers aren't a scope question for
Owl BI at all — there's no compute to sell. Not applicable, not deferred,
just a different business model (self-hosted, open source).

## Decisions made this session

1. **Apps vs. workspace** — add a publish step distinct from editing, so
   in-progress changes don't affect what production viewers see. Decided,
   not designed or built yet.
2. **Usage metrics + audit log** — instrument at the reverse proxy /
   FastAPI core as those are built, not retrofitted later. Decided, not
   built yet (the proxy itself doesn't exist yet — see architecture.md §9).
3. **Alerts & subscriptions** — kept open as "maybe later," not committed
   either way. Requires headless-rendering infrastructure Owl BI has no
   other reason to build yet.
4. **Deployment pipelines** — build an in-platform dev/test/prod promotion
   feature, rather than relying on git alone. This is a genuine scope
   addition; it needs its own design pass (data model for environments,
   who can promote, what exactly gets promoted) before any code gets
   written for it.

## New open questions (companions to architecture.md §8)

- **App publish model**: what gets versioned/promoted when a workspace
  editor "publishes" — the dashboard file itself? A pointer to a git ref?
  A full snapshot copied server-side? Undecided.
- **In-platform promotion feature**: environments per workspace or per
  dashboard? Who has permission to promote? Does promoting a dashboard
  also promote the dataset config it depends on? Undecided — flagged as
  in-scope, not yet designed.
- **Usage/audit log schema**: what exactly gets captured per
  request — dashboard id, viewer, workspace, timestamp, and (for RLS
  auditing purposes) the filter values applied? Where does it get stored
  and queried from? Undecided.
