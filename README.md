# Course Enrollment & Revenue Dashboard

This project processes course and enrollment CSV data into an enrollment report and course summary, then visualizes the results in an interactive **Streamlit** dashboard with charts built using **Plotly**.

## What it does

1. **`main.py`** — Reads course and enrollment files, applies business rules (valid course, valid date, payment outcome, capacity / waitlist), and writes:
   - `enrollment_report.csv` — one row per enrollment with a derived `status`
   - `course_summary.json` — per-course aggregates (enrolled count, remaining seats, revenue)

2. **`app.py`** — Streamlit app that loads those outputs and presents KPIs, filters, charts, tables, CSV downloads, and simple alerts (for example failed-payment spikes).

3. **`test.py`** — Unit tests for `process_enrollments` in `main.py`.

## Requirements

- Python 3.10+ recommended
- Packages:

```bash
pip install pandas streamlit plotly
```

## Input data

### Courses (`course_data.csv` by default in `main.py`)

| Column            | Description                          |
|-------------------|--------------------------------------|
| `course_id`       | Unique course identifier             |
| `course_name`     | Display name                         |
| `available_seats` | Maximum enrollments counted as seats |
| `course_fee`      | Fee used for revenue when paid       |

### Enrollments (`enrollment_data.csv` by default in `main.py`)

| Column             | Description                                      |
|--------------------|--------------------------------------------------|
| `student_id`       | Student identifier (also in enrollment report) |
| `course_id`        | Target course                                    |
| `enrollment_date`  | `YYYY-MM-DD` (invalid dates are rejected)        |
| `payment_status`   | e.g. `PAID`, `FAILED`                            |

Other columns (e.g. `enrollment_id`) may exist in the source CSV; processing uses the columns above.

## Enrollment statuses (report)

Processing sets each row’s `status` roughly as follows:

- **`INVALID_COURSE`** — `course_id` not in the course catalog  
- **`INVALID_DATE`** — `enrollment_date` not valid `YYYY-MM-DD`  
- **`PAYMENT_FAILED`** — `payment_status` is `FAILED`  
- **`WAITLISTED`** — payment succeeded but course is already at capacity  
- **`CONFIRMED`** — successful enrollment counted toward seats and revenue  

The dashboard maps some of these to payment groups (paid / failed / waitlisted / other) for charts and filters.

## How to run

### 1. Generate report and summary

From the project directory:

```bash
python main.py
```

By default this reads `course_data.csv` and `enrollment_data.csv` and overwrites `enrollment_report.csv` and `course_summary.json` in the same folder.

To use other files, change the paths in the `if __name__ == "__main__":` block in `main.py`, or import `process_enrollments` and call it with your paths.

### 2. Launch the dashboard

Ensure `enrollment_report.csv` and `course_summary.json` exist (run step 1 first if needed):

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

The app expects:

- **`enrollment_report.csv`** — must include `course_id` and `status`; `student_id` is optional (filled with empty string if missing). An optional **`enrollment_date`** column enables the “revenue over time” chart when present and parseable.

- **`course_summary.json`** — object keyed by `course_id`, each value with fields such as `course_name`, `capacity`, `enrolled`, `remaining_seats`, `revenue` (as produced by `main.py`).

### 3. Run tests

```bash
python -m unittest test.py
```

Tests create temporary `test_courses.csv` and `test_enrollments.csv` and also write `enrollment_report.csv` and `course_summary.json` when `process_enrollments` runs; run tests from the project directory and be aware they overwrite those default outputs if you rely on them for the dashboard.

## Project layout

| File                    | Role                                      |
|-------------------------|-------------------------------------------|
| `main.py`               | Enrollment processing pipeline            |
| `app.py`                | Streamlit dashboard                       |
| `test.py`               | Unit tests                                |
| `course_data.csv`       | Sample course catalog                     |
| `enrollment_data.csv`   | Sample enrollments                        |
| `enrollment_report.csv` | Generated enrollment report               |
| `course_summary.json`   | Generated course aggregates               |

