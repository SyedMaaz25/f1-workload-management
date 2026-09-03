# F1 Team Workload Management System

Tracks employee workload, maps it to projects/tasks and forecasts 30 day resource availability for an F1 team (Drivers, Strategists, Mechanics, Engineers, Managers, Sponsors).

## Run it
- pip install faker fastapi uvicorn
- python seed_data.py # employees, projects, tasks
- python seed_step2.py # assignments + 30 days of time logs
- uvicorn app:app --reload # API at localhost:8000/docs
- Then open `dashboard.html` in a browser (uvicorn must be running).

## How it works
- **Current workload**: 7-day rolling average of logged hours vs. 8hr/day standard capacity. Logs are daily-batched (satisfies 24hr latency requirement, no real-time tracking needed).
- **Forecast (30-day)**: trend extrapolation from the last 30 days, adjusted for known project end-dates (capacity frees up when a project ends, regardless of trend).
- **API**: `/workload/current`, `/workload/forecast`, `/employees`, `/projects` employee_id see `/docs` for full schema.
- **Dashboard**: live bar chart (current util, color-coded by status), table, per-employee forecast line.

## Key assumptions
- 8hr/day, 5-day week standard capacity, no weekend logging
- Forecast only knows about *currently assigned* work employee_id no visibility into future pipeline (a real limitation; F1 race calendars are known in advance and could feed this)
- Role→task-type affinity is fixed (e.g. Mechanics don't take Sponsor Meetings)