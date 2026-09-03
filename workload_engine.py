import sqlite3
from datetime import date, timedelta

DB_PATH = "f1_workload.db"

ROLLING_WINDOW_DAYS = 7

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_planned_utilization(conn):
    """Planned % of capacity allocated, from task_assignments."""
    rows = conn.execute("""
        SELECT e.employee_id, e.name, e.role,
               COALESCE(SUM(a.allocated_pct), 0) AS planned_pct
        FROM employees e
        LEFT JOIN task_assignments a ON e.employee_id = a.employee_id
        WHERE e.active = 1
        GROUP BY e.employee_id
    """).fetchall()
    return {r["employee_id"]: dict(r) for r in rows}

def get_actual_utilization(conn, window_days=ROLLING_WINDOW_DAYS):
    """Actual % of capacity used, from time_logs, trailing window."""
    cutoff = (date.today() - timedelta(days=window_days)).isoformat()
    rows = conn.execute("""
        SELECT e.employee_id, e.name, e.role, e.standard_daily_hours,
               COALESCE(SUM(t.hours), 0) AS logged_hours,
               COUNT(DISTINCT t.log_date) AS days_logged
        FROM employees e
        LEFT JOIN time_logs t ON e.employee_id = t.employee_id AND t.log_date >= ?
        WHERE e.active = 1
        GROUP BY e.employee_id
    """, (cutoff,)).fetchall()

    result = {}
    for r in rows:
        r = dict(r)
        working_days = count_weekdays(window_days)
        expected_hours = r["standard_daily_hours"] * working_days
        actual_pct = round((r["logged_hours"] / expected_hours) * 100, 1) if expected_hours > 0 else 0
        r["actual_pct"] = actual_pct
        result[r["employee_id"]] = r
    return result

def count_weekdays(window_days):
    today = date.today()
    count = 0
    for i in range(window_days):
        d = today - timedelta(days=i)
        if d.weekday() < 5:
            count += 1
    return count

def classify(pct):
    if pct > 100:
        return "Overloaded"
    elif pct >= 70:
        return "Fully Utilized"
    elif pct >= 30:
        return "Partially Available"
    else:
        return "Available"

def build_workload_report(conn):
    planned = get_planned_utilization(conn)
    actual = get_actual_utilization(conn)

    report = []
    for emp_id, p in planned.items():
        a = actual.get(emp_id, {})
        planned_pct = p["planned_pct"]
        actual_pct = a.get("actual_pct", 0)
        report.append({
            "employee_id": emp_id,
            "name": p["name"],
            "role": p["role"],
            "planned_pct": round(planned_pct, 1),
            "actual_pct": actual_pct,
            "availability_pct": round(max(0, 100 - actual_pct), 1),
            "status": classify(actual_pct)
        })
    return sorted(report, key=lambda r: -r["actual_pct"])

if __name__ == "__main__":
    conn = get_conn()
    report = build_workload_report(conn)
    print(f"{'Name':<22}{'Role':<12}{'Planned%':<10}{'Actual%':<10}{'Available%':<12}{'Status'}")
    for r in report:
        print(f"{r['name']:<22}{r['role']:<12}{r['planned_pct']:<10}{r['actual_pct']:<10}{r['availability_pct']:<12}{r['status']}")
    conn.close()