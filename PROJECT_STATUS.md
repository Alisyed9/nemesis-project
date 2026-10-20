# PySIEM — project status

Folder name: `Nemesis`  
Django project package: `pysiem`  
Current milestone: **Completed (Final Milestone 6)**

## Completed in Milestone 1

- Django project `pysiem` with apps `core` and `dashboard`
- SQLite, domain models, admin registration, README / requirements

## Completed in Milestone 2

- Auth.log-style parser (`core/services/parser.py`)
- Rule engine: regex on active `DetectionRule` plus failed-login burst correlation
- File collector creating `Event` rows
- Management command `python manage.py start_collector`

## Completed in Milestone 3

- Rule matches now persist `Alert` rows via `create_alert_for_event` (linked with `related_event`)
- High / Critical alerts get a `[HIGH]` / `[CRITICAL]` title prefix
- Terminal placeholder: High/Critical alerts print a clearly marked notice (no email yet)
- Collector tracks `alerts_created` and `high_critical_alerts`
- `start_collector` lists sources, warns if the log file is missing, and summarizes alerts
- Models in `core/models.py` were **not** changed

## Completed in Milestone 4

- Operator dashboard at `/` with Bootstrap 5 (CDN) dark theme
- Base template plus Overview / Events / Alerts navigation
- Overview: total events, total alerts, open alerts, recent tables, severity counts
- Alert rows use severity colors; each alert links to its `related_event`
- Operators can mark an alert `is_resolved=True` from list and detail pages
- Models and `core/services/` were **not** changed

## Current working features

- Admin CRUD for `LogSource`, `DetectionRule`, `Event`, `Alert`
- Parse Linux auth.log lines → `Event`
- Match `DetectionRule.pattern` (regex) and correlate ≥5 failed logins from one IP in 2 minutes
- Create `Alert` for every match, raised to the highest matched severity
- Follow or one-shot collect: `python manage.py start_collector` / `--once`
- High/Critical console notice at creation time
- Dark dashboard UI for reviewing events and resolving alerts

Public imports:

```python
from core.services import (
    parse_auth_log_line,
    evaluate_parsed_log,
    prepare_alert_data,
    create_alert_for_event,
    notify_high_severity_alert,
    ingest_log_source,
    run_collector,
)
```

## Exact models (`core.models`) — unchanged

| Model | Fields |
| --- | --- |
| `LogSource` | `name`, `file_path`, `source_type`, `is_active`, `created_at` |
| `DetectionRule` | `name`, `description`, `pattern`, `severity`, `is_active`, `created_at` |
| `Event` | `timestamp`, `source` (FK → `LogSource`), `message`, `raw_log`, `ip_address`, `username`, `severity` |
| `Alert` | `title`, `description`, `severity`, `related_event` (FK → `Event`), `is_resolved`, `created_at` |

## How to run

1. Create an active `LogSource` in `/admin/` with `file_path` pointing at an auth.log-style file.
2. Add `DetectionRule` rows (`pattern` is a regex). Use severity High/Critical for noisy signatures you care about.
3. `python manage.py start_collector --once` or `python manage.py start_collector`
4. Review the dashboard at http://127.0.0.1:8000/ (admin still at `/admin/`)

## Completed in Milestone 5

- Rules Manager at `/rules/` with list, add, edit, and delete workflows
- Detection rule CRUD uses a Django `ModelForm` with success/error messages
- Alerts page filters by status and severity while preserving pagination state
- Alert rows show severity colors, resolution controls, and related event context
- Navigation links expose Rules and Alerts from every dashboard page
- Models and `core/services/` were **not** changed

## Completed in Final Milestone 6

- Added six realistic demo Detection Rules through `python manage.py seed_demo_data`
- Added tracked auth.log-style sample data at `sample_data/auth.log`
- Verified the complete sample flow: log file → parser → rule engine → Event + Alert → dashboard
- Improved empty states for Events, Alerts, Rules Manager, and dashboard tables
- Finalized README setup, feature, rule authoring, testing, and sample-flow instructions
- Added end-to-end collector coverage and demo-rule signature coverage
- Project status: **Completed**

## Final notes

- Collector file offsets remain in memory and reset when the process restarts.
- High/Critical notification delivery remains terminal-only for local development.

## Current project structure

```
Nemesis/
├── .gitignore
├── PROJECT_STATUS.md
├── README.md
├── manage.py
├── requirements.txt
├── static/
│   └── css/
│       └── dashboard.css
├── sample_data/
│   └── auth.log
├── templates/
│   ├── base.html
│   └── dashboard/
├── core/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── management/
│   │   └── commands/
│   │       ├── seed_demo_data.py
│   │       └── start_collector.py
│   ├── services/
│   │   ├── collector.py
│   │   ├── parser.py
│   │   └── rule_engine.py
│   └── migrations/
│       └── 0001_initial.py
├── dashboard/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── templatetags/
│   │   └── dashboard_extras.py
│   └── migrations/
└── pysiem/
    ├── asgi.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```
