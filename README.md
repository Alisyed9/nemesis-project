# Nemesis

Nemesis is a lightweight local Security Information and Event Management (SIEM) tool built with Django. It reads Linux `auth.log`-style files, parses security events, evaluates configurable detection rules, creates severity-based alerts, and presents the results in a dark operator dashboard.

## Features

- Auth-log parser with timestamps, usernames, IP addresses, and normalized messages
- Regex-based detection rules with Critical, High, Medium, and Low severity levels
- Failed-login burst correlation for repeated attempts from one IP
- Collector that supports one-shot ingestion or continuous polling
- Event and alert persistence in SQLite
- Dashboard with overview metrics, event details, alert filtering, and resolution actions
- Rules Manager with add, edit, delete, active/inactive, and validation workflows
- Six realistic demo rules and a sample `auth.log` file
- Django admin for managing sources, rules, events, and alerts

## Tech stack

- Python 3.11+
- Django 5.2
- SQLite
- Bootstrap 5 via CDN

## Setup

From the project root (`Nemesis`):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

If PowerShell blocks activation for the current terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run the dashboard

Create an administrator when needed:

```bash
python manage.py createsuperuser
```

Start Django:

```bash
python manage.py runserver
```

Open the dashboard at `http://127.0.0.1:8000/`.

- Dashboard: `/`
- Events: `/events/`
- Alerts: `/alerts/`
- Rules Manager: `/rules/`
- Admin: `/admin/`

## Run the sample flow

Install the six demo rules and register `sample_data/auth.log` as an active source:

```bash
python manage.py seed_demo_data
```

Then process the sample file once:

```bash
python manage.py start_collector --once
```

Refresh the dashboard to see the generated events and alerts. High and Critical alerts are also printed in the collector terminal.

The demo command is safe to run repeatedly: it updates the named sample source and rules instead of creating duplicates. Collector offsets are held in memory, so running a one-shot collection again intentionally reads the file again.

## Add detection rules

Use either method:

1. Open Rules Manager at `/rules/`, select **Add detection rule**, enter a name, regex or keyword pattern, severity, and active state.
2. Open `/admin/` and create a `DetectionRule` directly.

Rules are matched case-insensitively against the parsed event message. For example:

```text
Pattern: Failed password
Severity: High
```

Invalid regular expressions are skipped by the rule engine and logged as warnings.

## Run tests

Run the complete test suite:

```bash
python manage.py test
```

Run Django configuration checks:

```bash
python manage.py check
```

The tests cover parser/collector behavior, rule signatures, alert creation, dashboard filtering, alert resolution, and Rules Manager CRUD.

## Project structure

```text
Nemesis/
├── core/
│   ├── models.py
│   ├── services/
│   │   ├── collector.py
│   │   ├── parser.py
│   │   └── rule_engine.py
│   └── management/commands/
│       ├── seed_demo_data.py
│       └── start_collector.py
├── dashboard/
│   ├── forms.py
│   ├── views.py
│   └── tests.py
├── sample_data/auth.log
├── templates/
├── static/css/dashboard.css
├── PROJECT_STATUS.md
└── manage.py
```

## Local development notes

- SQLite database: `db.sqlite3`
- The development settings use `DEBUG = True`; change the secret key and deployment settings before production use.
- Collector file offsets are currently in memory and reset when the process restarts.
- Email/webhook delivery is intentionally outside this completed local milestone; high-severity notifications currently use the terminal.
