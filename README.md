# F1 Team Workload Management System

A workload management and resource forecasting system for an F1 team. It tracks employee workload, maps employees to projects/tasks, measures current utilization, and forecasts resource usage for the next 30 days.

## Features

* Tracks employees across 6 roles: Driver, Strategist, Mechanic, Engineer, Manager, Sponsor
* Maps employees → tasks → projects
* Daily-batched time logging to support **24-hour workload visibility**
* Calculates:

  * Planned utilization
  * Actual utilization
  * Available capacity
  * Workload status
* 30-day workload forecasting
* Forecast adjustment based on projects ending during the forecast period
* REST API with FastAPI
* Dashboard with workload charts, employee table, and forecast visualization

## Tech Stack
* Python
* SQLite
* FastAPI
* NumPy / Scikit-learn
* Faker
* Chart.js
* HTML/CSS/JavaScript

## Run Locally

```bash
pip install faker fastapi uvicorn numpy scikit-learn

python seed_data.py
python seed_step2.py

uvicorn app:app --reload
```

Then open `dashboard.html`.

API documentation:

`http://127.0.0.1:8000/docs`

## Forecasting Approach

The system uses the previous 30 days of logged workload to estimate the employee's workload trend for:

* 7 days
* 14 days
* 30 days

Known project end dates are also considered. When a project ends, its allocated workload is removed from the projected utilization.

## Key Assumptions

* Standard capacity = **8 hours/day**
* Working week = **5 days**
* Time logs are submitted daily rather than in real time
* Only the six specified F1 roles exist
* Role/task affinity is used to generate realistic assignments
* Future projects not yet assigned to employees are not included in the forecast

## Automation & AI Suggestions

### Non-Agentic

* Scheduled workload calculations
* Automatic alerts when utilization exceeds 100%

### Agentic

*  Recommend resource allocation
* Explain why an employee is recommended

## Project Structure

```text
├── seed_data.py
├── seed_step2.py
├── workload_engine.py
├── forecast_engine.py
├── app.py
├── dashboard.html
├── f1_workload.db
└── README.md
```