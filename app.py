from fastapi import FastAPI, HTTPException
from workload_engine import get_conn, build_workload_report
from forecast_engine import build_forecast_report
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="F1 Team Workload Management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/employees")
def list_employees():
    conn = get_conn()
    rows = conn.execute("SELECT employee_id, name, role, standard_daily_hours FROM employees WHERE active=1").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/projects")
def list_projects():
    conn = get_conn()
    rows = conn.execute("SELECT project_id, name, category, start_date, end_date, status FROM projects").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/workload/current")
def current_workload():
    """Current utilization: planned vs actual (7-day rolling), availability %, and status."""
    conn = get_conn()
    report = build_workload_report(conn)
    conn.close()
    return report

@app.get("/workload/current/{employee_id}")
def current_workload_for_employee(employee_id: int):
    conn = get_conn()
    report = build_workload_report(conn)
    conn.close()
    match = next((r for r in report if r["employee_id"] == employee_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Employee not found")
    return match

@app.get("/workload/forecast")
def forecast():
    """30-day forecast: trend-based projection adjusted for known project end dates."""
    conn = get_conn()
    report = build_forecast_report(conn)
    conn.close()
    return report

@app.get("/workload/forecast/{employee_name}")
def forecast_for_employee(employee_name: str):
    conn = get_conn()
    report = build_forecast_report(conn)
    conn.close()
    match = next((r for r in report if r["name"].lower() == employee_name.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail="Employee not found")
    return match

@app.get("/")
def root():
    return {
        "message": "F1 Team Workload Management API",
        "endpoints": ["/employees", "/projects", "/workload/current", "/workload/forecast"]
    }