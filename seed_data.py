import sqlite3
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

DB_PATH = "f1_workload.db"
ROLES = ["Driver", "Strategist", "Mechanic", "Engineer", "Manager", "Sponsor"]
STANDARD_DAILY_HOURS = 8

def create_schema(conn):
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS time_logs;
    DROP TABLE IF EXISTS task_assignments;
    DROP TABLE IF EXISTS tasks;
    DROP TABLE IF EXISTS projects;
    DROP TABLE IF EXISTS employees;

    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('Driver','Strategist','Mechanic','Engineer','Manager','Sponsor')),
        standard_daily_hours REAL NOT NULL DEFAULT 8,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE projects (
        project_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,  
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'active'
    );

    CREATE TABLE tasks(
        task_id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        work_type TEXT,  
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    );

    CREATE TABLE task_assignments (
        assignment_id INTEGER PRIMARY KEY,
        task_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        allocated_pct REAL,  -- planned % of employee's time allocated to this task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id),
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );

    -- Actual logged hours, batched daily (satisfies the 24hr-latency requirement:
    -- logs are written once per day, not streamed in real time)
    CREATE TABLE time_logs(
        log_id INTEGER PRIMARY KEY,
        employee_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        log_date TEXT NOT NULL,
        hours REAL NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
    );
    """)
    conn.commit()

def seed_employees(conn, number_per_role = 6):
    cur = conn.cursor()
    employee_Id = 1
    for role in ROLES:
        for _ in range(number_per_role):
            cur.execute(
                "INSERT INTO employees (employee_id, name, role, standard_daily_hours, active) VALUES (?,?,?,?,1)",
                (employee_Id, fake.name(), role, STANDARD_DAILY_HOURS)
            )
            employee_Id += 1
    conn.commit()
    return employee_Id - 1

PROJECT_CATEGORIES = ["Race Weekend", "Car Development", "Sponsor Activation", "Simulation & Testing"]
WORK_TYPES_BY_CATEGORY = {
    "Race Weekend": ["Pit Strategy", "Car Setup", "Data Analysis", "Driver Briefing"],
    "Car Development": ["Aero Design", "Component Testing", "CAD Modeling", "Build & Assembly"],
    "Sponsor Activation": ["Sponsor Meeting", "Brand Event", "Reporting"],
    "Simulation & Testing": ["Sim Session", "Telemetry Review", "Setup Optimization"]
}

def seed_projects_and_tasks(conn, n_projects=8):
    cur = conn.cursor()
    today = date.today()
    project_id = 1
    task_Id = 1
    task_ids_by_project = {}
    for _ in range(n_projects):
        category = random.choice(PROJECT_CATEGORIES)
        start = today - timedelta(days=random.randint(0, 20))
        end = start + timedelta(days=random.randint(10, 45))
        name = f"{category} - {fake.city()} GP" if category == "Race Weekend" else f"{category} #{project_id}"
        cur.execute(
            "INSERT INTO projects (project_id, name, category, start_date, end_date, status) VALUES (?,?,?,?,?,?)",
            (project_id, name, category, start.isoformat(), end.isoformat(), "active")
        )
        task_ids_by_project[project_id] = []
        for wt in WORK_TYPES_BY_CATEGORY[category]:
            cur.execute(
                "INSERT INTO tasks (task_id, project_id, name, work_type) VALUES (?,?,?,?)",
                (task_Id, project_id, f"{wt} - {name}", wt)
            )
            task_ids_by_project[project_id].append(task_Id)
            task_Id += 1
        project_id += 1
    conn.commit()
    return task_ids_by_project

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    n_employees = seed_employees(conn)
    task_ids_by_project = seed_projects_and_tasks(conn)
    print(f"Seeded {n_employees} employees across {len(ROLES)} roles.")
    print(f"Seeded {len(task_ids_by_project)} projects with tasks.")
    conn.close()
    print(f"Database created at {DB_PATH}")