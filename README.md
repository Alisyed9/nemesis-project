# Nemesis

**Nemesis** is a lightweight local SIEM (Security Information and Event Management) tool built with Django.  
It monitors log files, detects suspicious activities using customizable rules, generates alerts, and provides a clean dashboard for monitoring.

---

## Current Features (Up to Milestone 4)

- Log collection from files
- Parsing of Linux auth.log style logs
- Rule-based detection engine
- Alert generation with severity levels (Critical, High, Medium, Low)
- Basic correlation (e.g. multiple failed logins from same IP)
- Modern dark-themed Dashboard
- View recent Events and Alerts
- SQLite database

---

## Tech Stack

- **Backend:** Django
- **Database:** SQLite
- **Frontend:** Bootstrap 5 (CDN)
- **Language:** Python 3.10+

---

## Project Structure

```
Nemesis/
├── core/
│   ├── models.py
│   ├── services/
│   │   ├── collector.py
│   │   ├── parser.py
│   │   └── rule_engine.py
│   └── management/commands/start_collector.py
├── dashboard/
│   ├── views.py
│   └── templates/
├── PROJECT_STATUS.md
└── manage.py
```

---

## How to Run

1. **Clone / Extract the project**

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   # source venv/bin/activate     # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the server:**
   ```bash
   python manage.py runserver
   ```

7. **Start Log Collector (in another terminal):**
   ```bash
   python manage.py start_collector
   ```

8. Open browser: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Admin Panel

- URL: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- You can manage Log Sources, Detection Rules, Events, and Alerts from here.

---

## Next Steps (Upcoming)

- Rules Manager (Add/Edit/Delete rules from UI)
- Advanced Alerts page with filters
- Mark alerts as resolved
- Better reporting

---

## Notes

- Currently supports Linux `auth.log` style logs.
- Rules are regex based.
- This is an educational / portfolio project.
```
