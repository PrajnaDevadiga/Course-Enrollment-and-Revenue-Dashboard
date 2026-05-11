import pandas as pd
import json
from datetime import datetime


def valid_date(date_text):
    """
    Check whether the date is valid.
    Expected format: YYYY-MM-DD
    """
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def process_enrollments(courses_file, enrollments_file):
    """
    Process enrollment records and generate reports.
    """

    # Read CSV files
    courses_df = pd.read_csv(courses_file)
    enrollments_df = pd.read_csv(enrollments_file)

    # Convert courses into dictionary
    course_dict = {}

    for _, row in courses_df.iterrows():
        course_dict[row["course_id"]] = {
            "course_name": row["course_name"],
            "capacity": row["available_seats"],
            "fee": row["course_fee"],
            "enrolled": 0,
            "revenue": 0
        }

    processed_rows = []

    # Process each enrollment
    for _, row in enrollments_df.iterrows():

        enrollment_status = "CONFIRMED"

        course_id = row["course_id"]
        payment_status = row["payment_status"]
        enrollment_date = row["enrollment_date"]

        # Rule 1: Course must exist
        if course_id not in course_dict:
            enrollment_status = "INVALID_COURSE"

        # Rule 2: Date must be valid
        elif not valid_date(str(enrollment_date)):
            enrollment_status = "INVALID_DATE"

        else:
            course = course_dict[course_id]

            # Rule 3 & 4: FAILED payments
            if payment_status == "FAILED":
                enrollment_status = "PAYMENT_FAILED"

            else:
                # Rule 5: Waitlist logic
                if course["enrolled"] >= course["capacity"]:
                    enrollment_status = "WAITLISTED"
                else:
                    course["enrolled"] += 1
                    course["revenue"] += course["fee"]

        processed_rows.append({
            "student_id": row["student_id"],
            "course_id": course_id,
            "status": enrollment_status
        })

    # Create enrollment report CSV
    report_df = pd.DataFrame(processed_rows)
    report_df.to_csv("enrollment_report.csv", index=False)

    # Create course summary JSON
    summary_data = {}

    for course_id, details in course_dict.items():
        summary_data[course_id] = {
            "course_name": details["course_name"],
            "capacity": int(details["capacity"]),
            "enrolled": int(details["enrolled"]),
            "remaining_seats": int(details["capacity"] - details["enrolled"]),
            "revenue": int(details["revenue"])
        }

    with open("course_summary.json", "w") as json_file:
        json.dump(summary_data, json_file, indent=4)

    return report_df, summary_data


if __name__ == "__main__":
    process_enrollments("course_data.csv", "enrollment_data.csv")

    print("Processing completed successfully.")
    print("Generated:")
    print("1. enrollment_report.csv")
    print("2. course_summary.json")