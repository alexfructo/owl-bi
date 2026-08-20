# Owl BI — Architecture Notes

**Status:** brainstorm / early exploration. Nothing here is final — this is a
running log of the ideas discussed so far, kept to seed the project's design
doc and issues.

## 1. Origin & pitch

Alternative to Power BI, much simpler in scope: a platform to publish,
control access to, and embed dashboards built as Streamlit apps.

Motivation: no free/open source tool today covers the specific combination
of publishing + access control + embed with RLS for Python-based dashboards.
Power BI does this well but is closed, paid, and has visual customization
limits we've run into. The gap seems real, not over-ambition — the scope
just needs to stay disciplined (see [§7](#7-scope-guardrails)).

## 2. Roles & hierarchy

Two layers of roles, intentionally separate:

**Platform-level:**
- **Admin** — manages the platform itself
- **Creator** — publishes dashboards; some creators can also create
  workspaces, others can only use existing ones
- **Viewer** — consumes only

**Workspace-level** (independent from platform roles):
- **Admin** — full control, including managing dashboard permissions
- **Editor** — add / remove / edit dashboards
- **Viewer** — access to all dashboards published in the workspace

## 3. Core concepts

**Workspace**
Organizational unit. Groups dashboards and datasets. Some creators can
create workspaces; others only operate within ones they've been granted
access to.

**Dashboard**
A Streamlit app — either uploaded as a `.py` file or written in-platform via
an editor. Each dashboard runs as its own isolated process, on its own
port. The main application acts as a reverse proxy in front of all of them.

**Dataset**
Originally scoped like Power BI's import vs. DirectQuery model. In practice
it evolved into something simpler: a data connection consumed by a
dashboard via SDK. The import/DirectQuery distinction stopped making sense
once the runtime is already Python (Streamlit) fetching data on demand —
there's no separate "engine" to import into.

**Embed**
Dashboards can be embedded outside the platform using an authorization
token — no internal platform login required. The embed accepts parameters
that double as RLS filters.

## 4. Where we landed on architecture

### 4.1 Dashboard lifecycle (subprocess management)

Decision direction: isolated OS processes, not Docker containers, at least
for the current stage.

Reasoning:
- Docker per dashboard adds cold-start latency, dynamic port/network
  management, and orchestration complexity that isn't justified without a
  real orchestrator (K8s-level tooling) — overkill if creators are
  internal/trusted.
- Docker becomes worth it if/when isolation needs to cover untrusted
  third-party code, not just internal creators.
- A single shared Streamlit process ("blueprints" / multipage style) was
  considered and rejected — Streamlit shares process/session state, so one
  heavy query or bug would degrade every dashboard sharing that process.
  Isolation is the whole point; don't give it up for convenience.

Chosen middle ground: isolated processes + resource limits (cgroups/ulimit),
with a pool + idle timeout — spin up on demand, tear down after inactivity,
reuse ports.

Known failure modes to design around:
- **Port/spawn race conditions** — two simultaneous requests for the same
  not-yet-running dashboard; needs a per-dashboard lock during spawn.
- **Zombie processes** — if the FastAPI parent dies without cleanup,
  children survive. Needs a death-signal mechanism (`PR_SET_PDEATHSIG` on
  Linux) or a watchdog.
- **Resource exhaustion** — a buggy dashboard (infinite loop, memory leak)
  can take down the host without per-process resource limits
  (`resource.setrlimit`).
- **Reconciliation on boot** — after a FastAPI restart, previously
  "running" instances in the state table may be stale; verify PIDs still
  exist (`psutil.pid_exists`) before trusting the registry.
- **Multi-instance FastAPI (future)** — "local port / local PID" breaks
  down if the API scales horizontally. Not a now-problem, but the state
  model should record which host/instance owns a process, not just the
  port, to avoid a rework later.

### 4.2 Proxy

FastAPI acts as reverse proxy for `/dashboard/{id}/*` → `localhost:{port}`.
Must handle WebSocket upgrade, not just plain HTTP — Streamlit relies on WS
for session state, and this is typically the trickiest part to get right
in a hand-rolled proxy.

### 4.3 RLS & the dataset problem

Current state (needs rework): RLS is "kind of implemented" — an
LLM-assisted first pass that maps a field name to a parameter received via
the SDK, injecting it as a condition into the query at dashboard-code
level.

Problems identified with this approach:
- **SQL injection risk** if parameters flow into queries without strict
  bind-parameter handling.
- **Trust boundary is wrong** — RLS enforcement lives inside the
  dashboard's own code. If a creator writes free-form Python and skips the
  SDK call (on purpose or by mistake), RLS is silently bypassed.
  Enforcement based on "hoping the app cooperates" is fragile.
- **Multi-query dashboards** — if a dashboard hits the same dataset with
  several queries/joins, the field→parameter mapping must be applied
  consistently everywhere, or a second query/join leaks data.
- **Unvalidated field targeting** — the field that "receives" the
  parameter should come from a whitelist defined by the dataset owner, not
  be arbitrary/attacker-influenceable from the token.

Direction we agreed on: move query execution and RLS enforcement into a
separate **dataset service**, not the dashboard process.

- Dashboard/SDK → HTTP call to `POST /internal/datasets/{id}/query`
  (initially just a module inside the existing FastAPI monolith, not a
  separate deployable — can evolve into its own service later if load
  justifies it)
- Credentials for actual data sources live only in this service —
  dashboards never see a raw connection string, only a dataset id/token
- RLS logic is the same as today, just relocated: applied centrally, at
  the one place all queries pass through
- Side benefits gained for free: connection pooling per data source (not
  per Streamlit process), query timeout/row-limit enforcement, response
  caching by `(dataset_id, hash of RLS filters)`, rate limiting per
  workspace/user

Incremental path (doesn't require infra changes up front):
1. Dataset module inside the existing FastAPI monolith; sync, with an
   in-memory or Redis TTL cache
2. Move heavy queries off the main event loop (threadpool/processpool, or
   a simple queue like Celery/RQ) if latency becomes a problem
3. Split into a real standalone service, horizontally scaled, only if
   volume demands it

### 4.4 Current stack (as of this discussion)

- Monolith, FastAPI
- Dashboards run as subprocesses
- React frontend, built and served by the same app

## 5. Open source direction

Decided to explore releasing this as open source rather than keeping it
internal-only. Researched existing tools to validate the gap (see
comparison table in the README) — closest analogs are Posit Connect
(closed/paid, similar publishing model) and Metabase/Superset (open
source, mature embed+RLS, but a visual query-builder paradigm, not
free-form Python).

Conclusion: no existing free/open source project combines workspace +
role-based access + isolated Streamlit publishing + token embed with RLS.
The gap is real.

Before opening the repo publicly, agreed priorities:
1. Harden the security-critical parts first — centralized RLS, credentials
   out of the dashboard subprocess (see §4.3)
2. Write the README/pitch early to validate interest, even before the code
   is "done"
3. Only then push the real repo public, once someone can clone and run it
   without embarrassment

Scope guardrails (see also §7): explicitly not trying to be a
visual/drag-and-drop BI tool or a data modeling layer (no DAX equivalent).
The pitch is "publishing infrastructure for Streamlit," not "Power BI
clone."

## 6. Naming & README

- Project name: **Owl BI 🦉**
- README drafted in English, following common open source Python project
  conventions (badges, quick start block, feature list with emoji,
  comparison table, architecture ASCII diagram, roadmap checklist,
  contributing/localization sections)
- Platform is being built i18n-ready from the start (translation keys, no
  hardcoded strings) — default language English, contributions for other
  locales welcome once the contribution workflow opens
- License: not yet decided — MIT/Apache 2.0 (broad adoption) vs. AGPL
  (open-core model, forces hosted forks to stay open) both on the table

## 7. Scope guardrails

Explicitly out of scope for now, to avoid Power-BI-style scope creep:
- No visual/drag-and-drop report builder — dashboards are Streamlit code
- No data modeling layer (relationships, DAX-equivalent) — that logic
  lives in dashboard code and/or the dataset layer
- No attempt to match Power BI's visual customization depth as a v1 goal

## 8. Open questions / not yet decided

- [x] Exact shape of the dataset service API — MVP implemented in
      `src/owl_bi/datasets/`: `POST /internal/datasets/{id}/query` takes
      `{filters, limit}`, returns `{rows}`. Filters are equality-only,
      restricted to a per-dataset column whitelist (`DatasetConfig.
      allowed_filters`) — no free-form SQL or operators from the caller.
      Still open: cache key design (§4.3's `(dataset_id, hash of RLS
      filters)` idea isn't built yet), and whether equality-only filters
      stay sufficient once real dashboards need ranges/IN-lists.
- [ ] License choice (MIT/Apache vs AGPL)
- [x] Auth mechanism between subprocess and FastAPI core — implemented as
      proposed: a single shared-secret bearer token via
      `OWL_BI_INTERNAL_TOKEN`. Known limitation, not yet addressed: any
      caller with the token can query any registered dataset, subject
      only to that dataset's filter whitelist — fine while the caller is
      a trusted subprocess on the same host, revisit before multi-tenant
      hosting.
- [ ] Whether/when Docker becomes necessary (currently: only if isolating
      untrusted code becomes a requirement)
- [ ] Multi-instance FastAPI story (sticky routing vs. container
      orchestration) — deferred, not a current blocker
- [ ] Contribution workflow / `CONTRIBUTING.md` — planned for first public
      release, not written yet

## 9. Suggested next steps (code)

Candidates discussed for "what to build first":
- Dataset service module (FastAPI + centralized RLS)
- Subprocess/dashboard lifecycle manager + proxy
- Repo scaffolding (folder structure, docker-compose, config)
- SDK the dashboards will import to call the dataset service

No decision made yet on ordering — to be picked up in the next working
session.
