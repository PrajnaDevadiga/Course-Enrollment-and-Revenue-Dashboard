import unittest
import pandas as pd
import json
from main import process_enrollments


class TestCourseProcessing(unittest.TestCase):

    # Runs before every test case
    def setUp(self):

        # Sample courses data
        courses_data = pd.DataFrame({
            "course_id": ["C101", "C102"],
            "course_name": ["Python", "Data Science"],
            "available_seats": [2, 1],
            "course_fee": [5000, 7000]
        })

        # Save courses data into temporary CSV
        courses_data.to_csv("test_courses.csv", index=False)

    # ---------------------------------------------------
    # Test 1: Invalid course should be rejected
    # ---------------------------------------------------
    def test_invalid_course_rejected(self):

        enrollments_data = pd.DataFrame({
            "student_id": ["S1"],
            "course_id": ["INVALID"],
            "enrollment_date": ["2025-01-01"],
            "payment_status": ["PAID"]
        })

        enrollments_data.to_csv("test_enrollments.csv", index=False)

        report, summary = process_enrollments(
            "test_courses.csv",
            "test_enrollments.csv"
        )

        self.assertEqual(
            report.iloc[0]["status"],
            "INVALID_COURSE"
        )

    # ---------------------------------------------------
    # Test 2: Invalid date should be rejected
    # ---------------------------------------------------
    def test_invalid_date_rejected(self):

        enrollments_data = pd.DataFrame({
            "student_id": ["S1"],
            "course_id": ["C101"],
            "enrollment_date": ["2025-99-99"],
            "payment_status": ["PAID"]
        })

        enrollments_data.to_csv("test_enrollments.csv", index=False)

        report, summary = process_enrollments(
            "test_courses.csv",
            "test_enrollments.csv"
        )

        self.assertEqual(
            report.iloc[0]["status"],
            "INVALID_DATE"
        )

    # ---------------------------------------------------
    # Test 3: FAILED payment should not count
    # ---------------------------------------------------
    def test_failed_payment_not_counted(self):

        enrollments_data = pd.DataFrame({
            "student_id": ["S1"],
            "course_id": ["C101"],
            "enrollment_date": ["2025-01-01"],
            "payment_status": ["FAILED"]
        })

        enrollments_data.to_csv("test_enrollments.csv", index=False)

        report, summary = process_enrollments(
            "test_courses.csv",
            "test_enrollments.csv"
        )

        self.assertEqual(
            report.iloc[0]["status"],
            "PAYMENT_FAILED"
        )

        self.assertEqual(
            summary["C101"]["enrolled"],
            0
        )

    # ---------------------------------------------------
    # Test 4: Revenue calculation
    # ---------------------------------------------------
    def test_revenue_calculation(self):

        enrollments_data = pd.DataFrame({
            "student_id": ["S1"],
            "course_id": ["C101"],
            "enrollment_date": ["2025-01-01"],
            "payment_status": ["PAID"]
        })

        enrollments_data.to_csv("test_enrollments.csv", index=False)

        report, summary = process_enrollments(
            "test_courses.csv",
            "test_enrollments.csv"
        )

        self.assertEqual(
            summary["C101"]["revenue"],
            5000
        )

    # ---------------------------------------------------
    # Test 5: Remaining seats calculation
    # ---------------------------------------------------
    def test_remaining_seats_calculation(self):

        enrollments_data = pd.DataFrame({
            "student_id": ["S1"],
            "course_id": ["C101"],
            "enrollment_date": ["2025-01-01"],
            "payment_status": ["PAID"]
        })

        enrollments_data.to_csv("test_enrollments.csv", index=False)

        report, summary = process_enrollments(
            "test_courses.csv",
            "test_enrollments.csv"
        )

        self.assertEqual(
            summary["C101"]["remaining_seats"],
            1
        )

    # ---------------------------------------------------
    # Test 6: Waitlist logic
    # ---------------------------------------------------
    def test_waitlist_logic(self):

        enrollments_data = pd.DataFrame({
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C102", "C102", "C102"],
            "enrollment_date": [
                "2025-01-01",
                "2025-01-01",
                "2025-01-01"
            ],
            "payment_status": ["PAID", "PAID", "PAID"]
        })

        enrollments_data.to_csv("test_enrollments.csv", index=False)

        report, summary = process_enrollments(
            "test_courses.csv",
            "test_enrollments.csv"
        )

        self.assertEqual(
            report.iloc[1]["status"],
            "WAITLISTED"
        )


# Runs all test cases
if __name__ == "__main__":
    unittest.main()