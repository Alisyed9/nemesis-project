# PySIEM

Python Security Information & Event Manager — a Django project for ingesting logs, detecting threats, and reviewing alerts.

This repository folder is named **Nemesis**. The Django project package is **`pysiem`**.

## Milestone 1 (current)

Foundation only: project layout, SQLite, and core models (`LogSource`, `DetectionRule`, `Event`, `Alert`). Collector, parser, rule engine, and dashboard UI are **not** implemented yet.

## Requirements

- Python 3.11+
- pip

## Setup

From the project root (`Nemesis`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

On macOS/Linux, activate the venv with `source .venv/bin/activate` instead of the PowerShell script.

Open:

- Admin: http://127.0.0.1:8000/admin/

Use the admin site to create log sources, detection rules, events, and alerts.

## Apps

| App | Role |
| --- | --- |
| `core` | Domain models and (later) collection / detection |
| `dashboard` | Operator UI (later milestones) |

Import models from `core.models`:

```python
from core.models import Alert, DetectionRule, Event, LogSource, Severity
```

## Configuration

- Database: SQLite at `db.sqlite3` (`pysiem/settings.py`)
- Debug is on for local development. Change `SECRET_KEY` before any real deployment.
