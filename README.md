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
## Real-data validation (Kali Linux VM)

Nemesis was tested end to end on real logs exported from a Kali Linux virtual
machine (VMware), replacing the bundled sample data.

**How the data was collected**

Recent Kali releases may not ship a `/var/log/auth.log` file, so the systemd
journal was exported instead:

```bash
sudo journalctl --no-pager -o short > kali_full.log
```

The file was registered as a `LogSource` in the Django admin (absolute path)
and ingested with `python manage.py start_collector --once`.

**Result**

- Over 13,000 real log lines were parsed into normalized events.
- Detection rules generated alerts with Critical and High severities.
- Controlled test: three deliberately wrong passwords were entered at the Kali
  GUI login. All three attempts were ingested as
  `pam_unix(lightdm:auth): authentication failure` events with correct
  timestamps.

## Reliability improvements

**SQLite "database is locked" fix**

Running the collector while editing or deleting a log source in the Django
admin caused `OperationalError: database is locked`. SQLite allows a single
writer at a time, and deleting a `LogSource` cascades to all its events and
alerts. Fixed in three layers:

1. **Database configuration** (`settings.py`): WAL journal mode, a 20 second
   lock timeout, and `IMMEDIATE` transactions.
2. **Collector** (`core/services/collector.py`):
   - Each chunk of log lines is saved in one atomic transaction, so a failed
     attempt leaves no partial data.
   - Retry with back-off when the database is locked.
   - The file offset only advances after a successful save, so a failed chunk
     is retried on the next cycle.
   - The source list is reloaded every cycle, so sources deleted or disabled
     in the admin do not crash the collector.
3. **Admin** (`core/admin.py`): a `DatabaseBusyMixin` shows a friendly error
   message instead of a 500 page when the database is busy.

## Findings from real-data testing

- **Rule coverage gap:** the default `Failed password` rule matches SSH
  failures only. Local GUI login failures (`authentication failure`) need
  their own rule.
- **False positives:** the generic error/critical rule flags routine desktop
  errors as Critical, which causes alert fatigue. Severity needs tuning.
- **Self-generated alerts:** administrative `sudo` commands used to export the
  logs triggered the suspicious-sudo rule.
- **Local logins carry no IP address:** the `rhost` field is empty, so the
  IP-based failed-login burst correlation cannot fire. Correlation by source
  and time window is needed for local attacks.
- **Timestamps:** events keep the log's own timestamp (for example 02:07 UTC),
  while alerts use ingest time. This is expected.

## Next steps

- Add a rule for local authentication failures
  (`authentication failure|Failed password|FAILED LOGIN|Invalid user`).
- Tune or narrow the generic error and sudo rules.
- Persist collector offsets to avoid duplicate events after a restart.
- Time-window burst detection (for example 3 failures in 30 seconds).
- Live log forwarding (rsyslog) and PostgreSQL for larger data volumes.
