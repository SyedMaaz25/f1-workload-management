import sqlite3
import random
from datetime import date, timedelta

random.seed(42)
DB_PATH = "f1_workload.db"

# How many days back to generate actual time logs for
LOOKBACK_DAYS = 30

def get_employees(conn):
    return conn.execute("SELECT employee_id, role, standard_daily_hours FROM employees").fetchall()

def get_tasks(conn):
    return conn.execute("SELECT task_id, project_id, work_type FROM tasks").fetchall()

ROLE_WORK_TYPE_AFFINITY = {
    "Driver": ["Driver Briefing", "Sim Session", "Telemetry Review", "Sponsor Meeting", "Brand Event"],
    "Strategist": ["Pit Strategy", "Data Analysis", "Telemetry Review", "Setup Optimization"],
    "Mechanic": ["Build & Assembly", "Component Testing", "Car Setup"],
    "Engineer": ["Aero Design", "CAD Modeling", "Component Testing", "Setup Optimization", "Data Analysis"],
    "Manager": ["Reporting", "Sponsor Meeting", "Brand Event", "Driver Briefing"],
    "Sponsor": ["Sponsor Meeting", "Brand Event", "Reporting"]
}

def eligible_tasks_for_employee(role, tasks):
    allowed = set(ROLE_WORK_TYPE_AFFINITY.get(role, []))
    return [t for t in tasks if t[2] in allowed]

def seed_task_assignments(conn):
    cur = conn.cursor()
    employees = get_employees(conn)
    tasks = get_tasks(conn)
    aid = 1
    assignments_by_employee = {}  

    for emp_id, role, _ in employees:
        candidates = eligible_tasks_for_employee(role, tasks)
        if not candidates:
            continue
        # each employee is assigned something like 1-3 concurrent tasks
        n_tasks = random.choice([1, 1, 2, 2, 3])
        chosen = random.sample(candidates, min(n_tasks, len(candidates)))

        bucket = random.random()
        if bucket < 0.15:
            total_pct = random.uniform(105, 130)   # overloaded
        elif bucket < 0.35:
            total_pct = random.uniform(20, 50)     # underloaded / available
        else:
            total_pct = random.uniform(60, 100)    # normal range

        remaining = total_pct
        for i, task in enumerate(chosen):
            if i == len(chosen) - 1:
                pct = remaining
            else:
                pct = round(random.uniform(0.3, 0.7) * remaining, 1)
                remaining -= pct
            pct = max(pct, 5)
            cur.execute(
                "INSERT INTO task_assignments (assignment_id, task_id, employee_id, allocated_pct) VALUES (?,?,?,?)",
                (aid, task[0], emp_id, round(pct, 1))
            )
            assignments_by_employee.setdefault(emp_id, []).append((task[0], pct))
            aid += 1

    conn.commit()
    return assignments_by_employee

def seed_time_logs(conn, assignments_by_employee):
    cur = conn.cursor()
    employees = {e[0]: e for e in get_employees(conn)}
    log_id = 1
    today = date.today()

    for emp_id, assignments in assignments_by_employee.items():
        std_hours = employees[emp_id][2]
        for day_offset in range(LOOKBACK_DAYS, 0, -1):
            log_date = today - timedelta(days=day_offset)
            if log_date.weekday() >= 5:
                continue
            if random.random() > 0.9:
                continue

            total_pct = sum(pct for _, pct in assignments)
            day_hours_total = std_hours * (total_pct / 100) * random.uniform(0.85, 1.15)
            day_hours_total = min(day_hours_total, std_hours * 1.5)  

            for task_id, pct in assignments:
                share = pct / total_pct if total_pct > 0 else 0
                hours = round(day_hours_total * share, 2)
                if hours <= 0:
                    continue
                cur.execute(
                    "INSERT INTO time_logs (log_id, employee_id, task_id, log_date, hours) VALUES (?,?,?,?,?)",
                    (log_id, emp_id, task_id, log_date.isoformat(), hours)
                )
                log_id += 1

    conn.commit()
    return log_id - 1

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    assignments_by_employee = seed_task_assignments(conn)
    n_assignments = sum(len(v) for v in assignments_by_employee.values())
    print(f"Seeded {n_assignments} task assignments across {len(assignments_by_employee)} employees.")
    n_logs = seed_time_logs(conn, assignments_by_employee)
    print(f"Seeded {n_logs} daily time log entries over the last {LOOKBACK_DAYS} days.")
    conn.close()