# Owl BI 🦉

> Publishing infrastructure for Streamlit dashboards — workspaces, role-based
> access, and token-based embeds with row-level security.

![status](https://img.shields.io/badge/status-pre--alpha-lightgrey)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![license](https://img.shields.io/badge/license-TBD-lightgrey)

> **Note:** Owl BI is in the design/brainstorm stage — see
> [`docs/architecture.md`](docs/architecture.md) for the full notes. This
> README describes the intended shape of the project; nothing below is
> guaranteed to work yet, and things will change.

## Why

[Streamlit](https://streamlit.io/) is a great way to build data apps in
plain Python. What's missing is the layer around it: a way to **publish**
those apps, **control who can see what**, and **embed** them elsewhere —
without hand-rolling auth, reverse proxies, and row-level security for
every project.

Power BI covers this ground well, but it's closed, paid, and has visual
customization limits that Python-first teams keep running into. Metabase
and Superset are open source and mature, but they're built around a visual
query-builder paradigm — not free-form Python dashboards. Posit Connect is
the closest analog to what we want, but it's closed/paid too.

Owl BI aims to fill that specific gap: **workspace + role-based access +
isolated Streamlit publishing + token embed with RLS**, as a free and open
source project.

Owl BI is explicitly **not** trying to be a drag-and-drop report builder or
a data modeling layer. If you want that, use Metabase/Superset/Power BI.
Owl BI is for teams that are already writing dashboards in Python and just
need somewhere real to put them.

## Feature comparison

| | Owl BI | Power BI | Metabase / Superset | Posit Connect |
|---|---|---|---|---|
| 🆓 Free / open source | ✅ | ❌ | ✅ | ❌ |
| 🐍 Free-form Python dashboards | ✅ | ❌ | ❌ | ✅ |
| 📊 Plotly / Streamlit-native visuals | ✅ | ❌ | ❌ | ✅ |
| 🏢 Workspaces & role-based access | ✅ (planned) | ✅ | ✅ | ✅ |
| 🔒 Token embed with row-level security | ✅ (planned) | ✅ | ✅ | ⚠️ limited |
| 🧩 Visual / drag-and-drop builder | ❌ (by design) | ✅ | ✅ | ❌ |

## How it works (planned)

```
                     ┌─────────────────────────┐
                     │   React frontend (SPA)  │
                     └────────────┬────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │   FastAPI core (proxy,  │
                     │ auth, workspaces, RLS)  │
                     └──┬───────┬───────┬──────┘
                        │       │       │
             ┌──────────▼─┐ ┌───▼─────┐ ┌▼──────────┐
             │ Dashboard  │ │Dashboard│ │ Dashboard  │
             │ (Streamlit │ │(Streamlit│ │ (Streamlit│
             │  subproc,  │ │ subproc, │ │  subproc, │
             │  own port) │ │ own port)│ │  own port)│
             └──────┬─────┘ └────┬────┘ └─────┬──────┘
                    │            │             │
                    └─────────┬──┴──────┬──────┘
                               │         │
                     ┌─────────▼─────────▼──────┐
                     │   Dataset service (RLS,  │
                     │ pooling, caching, creds) │
                     └────────────┬──────────────┘
                                  │
                          data sources (SQL, etc.)
```

- Each dashboard is a Streamlit app running as its **own isolated OS
  process**, spun up on demand behind a FastAPI reverse proxy (WebSocket
  aware, since Streamlit relies on it for session state).
- Dashboards never touch data source credentials directly. They call a
  small SDK that hits an internal **dataset service**, which is the one
  place RLS, credentials, pooling, and caching live.
- Embeds authenticate via token, not platform login, and pass parameters
  that double as RLS filters — enforced centrally, not inside dashboard
  code.

See [`docs/architecture.md`](docs/architecture.md) for the full reasoning,
including the failure modes we're designing around (spawn races, zombie
processes, resource limits, RLS trust boundary) and the parts still
undecided.

## Quick start

There's no installable package yet, but the dataset service MVP is
runnable — see [`examples/toy_dashboard/README.md`](examples/toy_dashboard/README.md)
for a real (if manual) end-to-end walkthrough: a Streamlit dashboard
calling the dataset service, RLS-filtered by region, with no subprocess
lifecycle manager or reverse proxy in front of it yet.

```bash
pip install -e ".[dev]"
pytest
```

## Roadmap

- [x] Repo scaffolding (folder structure, docker-compose, config) — backend only so far, no frontend scaffolding yet
- [x] Dataset service module (FastAPI + centralized RLS) — MVP: equality filters against a whitelist, no caching yet
- [ ] Subprocess/dashboard lifecycle manager + reverse proxy
- [x] SDK for dashboards to call the dataset service — MVP
- [ ] Workspace & role-based access control
- [ ] Token-based embed with RLS
- [ ] React frontend
- [ ] i18n support (translation keys from day one)
- [ ] `CONTRIBUTING.md` and first public release

## Scope guardrails

To avoid Power-BI-style scope creep, Owl BI explicitly does **not** aim to:
- Provide a visual/drag-and-drop report builder — dashboards are Streamlit
  code
- Provide a data modeling layer (relationships, DAX-equivalent) — that
  logic lives in dashboard code and/or the dataset layer
- Match Power BI's visual customization depth as a v1 goal

## Localization

Owl BI is being built i18n-ready from the start — translation keys, no
hardcoded strings. Default language is English; contributions for other
locales are welcome once the contribution workflow opens.

## License

Not yet decided. Under consideration: MIT/Apache 2.0 (broad adoption) vs.
AGPL (open-core model, forces hosted forks to stay open).

## Contributing

Not open yet — `CONTRIBUTING.md` is planned for the first public release.
In the meantime, see [`docs/architecture.md`](docs/architecture.md) for
open questions and design discussion.
