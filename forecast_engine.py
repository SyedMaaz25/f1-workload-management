import sqlite3
from datetime import date, timedelta
from workload_engine import get_conn, count_weekdays
import numpy as np
from sklearn.linear_model import LinearRegression

FORECAST_DAYS = 30

def get_daily_actual_series(conn, employee_id, lookback_days=30):
    """Daily logged hours for an employee over the lookback window, as (day_index, hours)."""
    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    rows = conn.execute("""
        SELECT log_date, SUM(hours) as hours
        FROM time_logs
        WHERE employee_id = ? AND log_date >= ?
        GROUP BY log_date
        ORDER BY log_date
    """, (employee_id, cutoff)).fetchall()

    today = date.today()
    series = []
    for r in rows:
        d = date.fromisoformat(r["log_date"])
        day_index = (d - (today - timedelta(days=lookback_days))).days
        series.append((day_index, r["hours"]))
    return series

def linear_regression(points):
    if len(points) < 2:
        return 0.0, (points[0][1] if points else 0.0)

    X = np.array([[p[0]] for p in points])
    y = np.array([p[1] for p in points])

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0]
    intercept = model.intercept_
    return slope, intercept

def get_ending_projects_impact(conn, employee_id, forecast_start, forecast_days):
    rows = conn.execute("""
        SELECT a.allocated_pct, p.end_date
        FROM task_assignments a
        JOIN tasks t ON a.task_id = t.task_id
        JOIN projects p ON t.project_id = p.project_id
        WHERE a.employee_id = ?
    """, (employee_id,)).fetchall()

    impacts = []
    for r in rows:
        end_date = date.fromisoformat(r["end_date"])
        offset = (end_date - forecast_start).days
        if 0 <= offset <= forecast_days:
            impacts.append((offset, r["allocated_pct"]))
    return impacts

def forecast_employee(conn, employee_id, std_daily_hours, forecast_days=FORECAST_DAYS):
    series = get_daily_actual_series(conn, employee_id)
    slope, intercept = linear_regression(series)

    today = date.today()
    checkpoints = [7, 14, 30]
    impacts = get_ending_projects_impact(conn, employee_id, today, forecast_days)

    results = {}
    for cp in checkpoints:
        if cp > forecast_days:
            continue
        projected_hours = slope * (30 + cp) + intercept 
        projected_hours = max(projected_hours, 0)
        working_days = count_weekdays(cp)
        expected_hours = std_daily_hours * working_days
        projected_pct = round((projected_hours * working_days) / expected_hours * 100, 1) if expected_hours > 0 else 0

        pct_freed = sum(pct for offset, pct in impacts if offset <= cp)
        adjusted_pct = max(0, projected_pct - pct_freed)

        results[f"day_{cp}"] = {
            "trend_pct": min(projected_pct, 200),
            "adjusted_pct": round(min(adjusted_pct, 200), 1),
            "note": f"-{round(pct_freed,1)}% from ending project(s)" if pct_freed > 0 else None
        }
    return results

def build_forecast_report(conn):
    employees = conn.execute("SELECT employee_id, name, role, standard_daily_hours FROM employees WHERE active=1").fetchall()
    report = []
    for e in employees:
        f = forecast_employee(conn, e["employee_id"], e["standard_daily_hours"])
        report.append({"name": e["name"], "role": e["role"], "forecast": f})
    return report

if __name__ == "__main__":
    conn = get_conn()
    report = build_forecast_report(conn)
    print(f"{'Name':<22}{'Role':<12}{'Day7%':<10}{'Day14%':<10}{'Day30%':<10}Notes")
    for r in report:
        f = r["forecast"]
        d7 = f.get("day_7", {}).get("adjusted_pct", "-")
        d14 = f.get("day_14", {}).get("adjusted_pct", "-")
        d30 = f.get("day_30", {}).get("adjusted_pct", "-")
        note = f.get("day_30", {}).get("note") or ""
        print(f"{r['name']:<22}{r['role']:<12}{str(d7):<10}{str(d14):<10}{str(d30):<10}{note}")
    conn.close()