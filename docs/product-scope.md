# Owl BI — Product Scope vs. Power BI

**Status:** first deliberate pass at product scope, with a second
completeness pass covering categories the first pass missed (see
"Completeness pass" below), and a round-3 revision that closed the
license decision and reversed the in-platform promotion call (see
"Round 3" below). Until this doc,
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
| Branding/white-label of the platform chrome (logo, colors) | 🕓 | Minor, low priority. Self-hosters will likely want this eventually; not core to the publishing pitch. |

## Content discovery & trust

Not covered anywhere before this pass — Power BI has a whole layer for
"find content you have or don't have access to" that Owl BI has no story
for yet.

| Feature | Status | Notes |
|---|---|---|
| Search / home page listing dashboards you have access to, across workspaces | 🕓 | Genuine gap — nothing today says how a viewer finds what they can see once there's more than a couple of workspaces. Not glamorous, but arguably needed even at v1 scale, unlike most items in this doc. Worth revisiting sooner than the 🕓 label implies. |
| Favorites / recently viewed | 🕓 | Minor, personal-productivity feature — low priority |
| Endorsement / certification badges (Power BI's "promoted" vs. "certified" content) | 🕓 | Trust signal for governance at scale. Not urgent while workspace/role access control already gates who sees what; revisit if content volume makes "which dashboard is the real one" a real problem. |
| Discoverability of content you don't have access to (request-access flow) | 🕓 | Bundled with search above — same open question, not designed |

## Automation & APIs

| Feature | Status | Notes |
|---|---|---|
| Management/automation REST API (provision workspaces, dashboards, roles, datasets programmatically — e.g. from CI/CD or Terraform-style tooling) | 🕓 | Distinct from the internal dataset-query API already built (`src/owl_bi/datasets/api.py`), which exists only for dashboards to fetch RLS-filtered data. Some backend for the web UI to call will exist regardless; whether it's stabilized and documented as a *public* automation API is a separate, undecided question. |

## Data refresh & connectivity

| Feature | Status | Notes |
|---|---|---|
| Scheduled dataset refresh | N/A | Doesn't map 1:1 — Streamlit fetches on demand, so "refresh" is whatever cadence the dashboard's own code chooses. The dataset service's planned response cache (architecture.md §4.3) is the closest analog, and it's already ✅ in scope. |
| Dataflows (reusable prep pipelines) | ❌ | This *is* the data modeling layer — excluded by the existing §7 guardrail |
| On-premises data gateway | 🕓 | Only matters once a real data source sits behind a firewall the dataset service can't reach directly. Might not need a dedicated gateway concept at all — "wherever the dataset service is hosted" may already solve it. Revisit if it comes up for real. |
| Real-time streaming / push datasets (live-updating tiles, not page-load queries) | 🕓 | Genuinely different shape from the pull/on-demand model already decided (dataset service answers a query when a dashboard asks). Continuous push would need its own delivery mechanism (websocket fan-out, a streaming buffer) — not a small extension of the current design. Low priority until a real use case shows up. |
| Shared/reusable datasets across many dashboards | ✅ implicit | Already how the dataset service works — register a dataset once, any dashboard can query it (subject to its own filter whitelist). No extra feature needed; this is what Power BI calls a "certified shared dataset," Owl BI gets it for free from the architecture. |

## Interactivity & report features

| Feature | Status | Notes |
|---|---|---|
| Bookmarks, drillthrough | ❌ | These are report-authoring features. In Owl BI a dashboard is Streamlit code, so navigation/interactivity is the dashboard author's job, not the platform's — consistent with "dashboards are Streamlit code" |
| Q&A / natural language query / Copilot | ❌ | Squarely inside the "no DAX-equivalent modeling / no BI magic" guardrail. Worth noting Power BI's own Q&A is being retired in favor of Copilot (Dec 2026) — not a feature worth chasing even on Power BI's own roadmap. |
| Mobile-optimized layout | 🕓 | Streamlit has some responsiveness already; platform's job is mostly "don't break it in the proxy," not a dedicated mobile feature |
| Custom visuals / visual marketplace | ✅ implicit | Already solved by construction — a dashboard is Plotly/any-Python-plotting-library code, so there's no marketplace to build; every visual Python can produce is already "supported." |
| Multi-source dashboards (one dashboard querying several datasets) | ✅ implicit | Already just code — a dashboard calls the SDK against however many `dataset_id`s it needs. No "composite model" feature required, unlike Power BI where this is a first-class modeling concept. |

## Export & offline access

Missing from the first pass entirely, despite being flagged in chat —
adding it properly here.

| Feature | Status | Notes |
|---|---|---|
| Raw data export (CSV/Excel) from within a dashboard | ✅ implicit | Already available to any dashboard author via `st.download_button` — dashboard-code responsibility, not a platform feature, consistent with "dashboards are Streamlit code" |
| Whole-dashboard export/snapshot (render the live app to a static PDF/image) | 🕓 | Real gap, distinct from raw data export — would need the same headless-rendering capability as alerts/subscriptions above. Bundle with that "maybe later" bucket rather than deciding separately. |
| Paginated / pixel-perfect reports (Power BI Report Builder / legacy SSRS model) | ❌ | Not a fit for a Streamlit-based platform at all — pixel-perfect fixed-layout printing is a fundamentally different rendering model. Not worth building even long-term. |

## Alerts & delivery

| Feature | Status | Notes |
|---|---|---|
| Data alerts (threshold-based notifications) | 🕓 **logged as "maybe later"** | Decided this session: not building now, not closing the door. Would need a threshold-evaluation engine plus a way to read a live Streamlit app's state outside a browser session — real infra, not a small add-on. |
| Subscriptions (scheduled email snapshot) | 🕓 **logged as "maybe later"** | Same bucket as alerts — needs headless rendering of a live Streamlit app (e.g. via a browser automation tool) to produce a static snapshot. Nontrivial, not started. |

## Deployment & lifecycle

| Feature | Status | Notes |
|---|---|---|
| Deployment pipelines (promote a dashboard dev → test → prod) | ❌ **revised** | Originally decided in-platform; reversed after a "how would Linus Torvalds see this" review flagged it as reinventing what `git` already does for free (branch/PR/merge). No in-platform staging UI — promotion is a branch/PR workflow outside the platform. See "Decisions made this session" below. |

## Governance & admin

| Feature | Status | Notes |
|---|---|---|
| Usage metrics (who viewed which dashboard, when) | ✅ **new** | Decided this session: instrument at the reverse proxy (architecture.md §4.2) as it's built — that's the one chokepoint all dashboard traffic already passes through, so it's cheap now and expensive to retrofit later. |
| Audit log (workspace created, permissions changed, dataset registered, etc.) | ✅ **new** | Same reasoning — log at the FastAPI core as actions happen, not bolted on after the fact. |
| Tenant-wide admin settings/portal | 🕓 | Deferred until there's more than a couple of settings to actually administer |
| Capacity management (Premium-style compute tiers) | ❌ | Doesn't apply to a self-hosted open source model — whoever runs Owl BI owns the hardware. Per-dashboard resource limits (cgroups/ulimit, architecture.md §4.1) already cover "don't let one dashboard take down the host"; there's no capacity *product* to build on top of that. |
| Sensitivity labels / data classification / lineage & impact analysis (which dashboards depend on this dataset, before I change it) | 🕓 | Enterprise governance feature. A cheap version — "list dashboards that reference dataset X" — becomes easy once dataset configs live in real storage instead of code (see `DatasetRegistry` in `src/owl_bi/datasets/registry.py`, currently in-memory only). Not needed yet, worth remembering once that registry gets a real backing store. |

**Multi-tenant hosted Owl BI vs. self-hosted single-tenant**: everything
in this doc assumes Owl BI is self-hosted by the team that uses it — the
usual open source model. If someone wanted to run Owl BI itself as a
hosted service *for other people* (an Owl-BI-as-a-SaaS business), that's
a distinct product shape nothing here is designed for, and it sharpens an
already-known gap: the internal dataset-service token is a single
shared secret today (architecture.md §8), fine for one trusted deployment,
not for isolating unrelated tenants from each other. Not a current
priority — flagged so it isn't rediscovered as a surprise later.

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
4. ~~Deployment pipelines — build an in-platform dev/test/prod promotion
   feature, rather than relying on git alone.~~ **Reversed in round 3**,
   see below.

## Completeness pass (round 2, same session)

The first pass missed whole categories: content discovery/trust,
automation APIs, real-time streaming, and export — added above. No new
scope *decisions* came out of this round, just gaps that needed a status
(mostly 🕓, a couple of ✅-implicit confirmations that no new feature is
actually needed, and one clean ❌ for paginated reports). The one thing
worth calling out: **version history / rollback of a published
dashboard** isn't a separate line item — it's the same problem as the App
publish model below, not a new one, so it's not listed twice.

## Round 3: license decided, promotion decision reversed

Prompted by a "how would Linus Torvalds and Richard Stallman look at this
project" review (see chat history — not reproduced here, the point is the
conclusions):

- **License**: closed. AGPL-3.0-or-later — see `LICENSE` and
  architecture.md §6. Was flagged as a decision being made *by omission*
  by leaving it "TBD"; Owl BI's own pitch (infrastructure people run as a
  service) is close to the textbook case the AGPL's network-use clause
  exists for.
- **Deployment pipelines: reversed.** Round-1 decided an in-platform
  dev/test/prod promotion feature. On reflection that was reinventing
  what `git` already does — a dashboard is a `.py` file, "promote to
  prod" is a merge. No in-platform staging UI gets built. This also
  collapses the "App publish model" open question below: publishing an
  App now just means pointing it at a git ref (branch or tag), not
  designing a bespoke versioning/snapshot mechanism.

## New open questions (companions to architecture.md §8)

- **App publish model**: now scoped down by the round-3 reversal above —
  an App points at a git ref (branch/tag) rather than a platform-managed
  snapshot. Still undecided: which ref convention (e.g. a `published`
  branch per dashboard? a tag the editor pushes?), what triggers the
  platform to notice a new ref exists (webhook vs. poll), and who's
  authorized to move it. Smaller question than before, but not zero.
- **Usage/audit log schema**: what exactly gets captured per
  request — dashboard id, viewer, workspace, timestamp, and (for RLS
  auditing purposes) the filter values applied? Where does it get stored
  and queried from? Undecided.
