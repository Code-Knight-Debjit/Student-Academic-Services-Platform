"""
Tests for Student Academic Services Platform - results app.
"""

from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

from results.models import (
    Student,
    StudentMetadata,
    Course,
    Result,
    Paper_Seeing,
    UploadHistory,
    RevaluationConfiguration,
    RevaluationRequest,
    PaperSeeingConfiguration,
    PaperSeeingRequest,
    MakeupExamConfiguration,
    MakeupExamRequest,
    StudentNotification,
    AuditLog,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def make_student(usn="1RV21CS001", name="Test Student", department="CSE", semester=3):
    return Student.objects.create(usn=usn, name=name, department=department, semester=semester)


def make_course(code="CS301", title="Data Structures", semester=3, credits=4):
    return Course.objects.create(course_code=code, course_title=title, semester=semester, credits=credits)


def make_result(student, course, marks=75.00, semester=3):
    return Result.objects.create(
        student=student,
        course=course,
        final_cie_marks=Decimal(str(marks)),
        semester=semester,
        academic_year="2023-24",
        scheme="2021",
    )


# ---------------------------------------------------------------------------
# Student Model Tests
# ---------------------------------------------------------------------------

class StudentModelTest(TestCase):

    def test_create_student(self):
        student = make_student()
        self.assertEqual(student.usn, "1RV21CS001")
        self.assertEqual(student.name, "Test Student")

    def test_student_str(self):
        student = make_student()
        self.assertIn("1RV21CS001", str(student))
        self.assertIn("Test Student", str(student))

    def test_usn_is_primary_key(self):
        student = make_student()
        self.assertEqual(student.pk, "1RV21CS001")

    def test_usn_validator_rejects_short_usn(self):
        student = Student(usn="SHORT", name="Bad Student")
        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_usn_validator_rejects_special_chars(self):
        student = Student(usn="1RV21CS@01", name="Bad Student")
        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_usn_validator_accepts_valid_usn(self):
        student = Student(usn="1RV21CS001", name="Good Student")
        try:
            student.full_clean()
        except ValidationError:
            self.fail("Valid USN raised ValidationError")

    def test_ordering_by_usn(self):
        make_student("1RV21CS003", "Charlie")
        make_student("1RV21CS001", "Alice")
        make_student("1RV21CS002", "Bob")
        usns = list(Student.objects.values_list("usn", flat=True))
        self.assertEqual(usns, sorted(usns))

    def test_auto_timestamps(self):
        student = make_student()
        self.assertIsNotNone(student.created_at)
        self.assertIsNotNone(student.updated_at)


# ---------------------------------------------------------------------------
# StudentMetadata Model Tests
# ---------------------------------------------------------------------------

class StudentMetadataModelTest(TestCase):

    def setUp(self):
        self.student = make_student()

    def test_create_metadata(self):
        meta = StudentMetadata.objects.create(
            student=self.student,
            dob=date(2002, 5, 15),
            admission_route="KCET",
        )
        self.assertEqual(meta.student, self.student)
        self.assertEqual(meta.admission_route, "KCET")

    def test_metadata_str(self):
        meta = StudentMetadata.objects.create(student=self.student, dob=date(2002, 5, 15))
        self.assertIn("1RV21CS001", str(meta))

    def test_one_to_one_relationship(self):
        StudentMetadata.objects.create(student=self.student, dob=date(2002, 5, 15))
        with self.assertRaises(Exception):
            StudentMetadata.objects.create(student=self.student, dob=date(2002, 6, 20))

    def test_cascade_delete(self):
        StudentMetadata.objects.create(student=self.student, dob=date(2002, 5, 15))
        self.student.delete()
        self.assertEqual(StudentMetadata.objects.count(), 0)

    def test_invalid_admission_route(self):
        meta = StudentMetadata(student=self.student, dob=date(2002, 5, 15), admission_route="INVALID")
        with self.assertRaises(ValidationError):
            meta.full_clean()


# ---------------------------------------------------------------------------
# Course Model Tests
# ---------------------------------------------------------------------------

class CourseModelTest(TestCase):

    def test_create_course(self):
        course = make_course()
        self.assertEqual(course.course_code, "CS301")
        self.assertEqual(course.credits, 4)

    def test_course_str(self):
        course = make_course()
        self.assertIn("CS301", str(course))
        self.assertIn("Data Structures", str(course))

    def test_unique_course_code(self):
        make_course()
        with self.assertRaises(Exception):
            make_course()  # duplicate course_code

    def test_ordering(self):
        make_course("CS302", "Algorithms", semester=3)
        make_course("CS201", "OOP", semester=2)
        make_course("CS301", "Data Structures", semester=3)
        courses = list(Course.objects.values_list("course_code", flat=True))
        # Should be ordered by semester then course_code
        self.assertEqual(courses[0], "CS201")


# ---------------------------------------------------------------------------
# Result Model Tests
# ---------------------------------------------------------------------------

class ResultModelTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.course = make_course()

    def test_create_result(self):
        result = make_result(self.student, self.course)
        self.assertEqual(result.final_cie_marks, Decimal("75.00"))
        self.assertEqual(result.student, self.student)

    def test_result_str(self):
        result = make_result(self.student, self.course)
        self.assertIn("1RV21CS001", str(result))
        self.assertIn("CS301", str(result))

    def test_unique_together_student_course(self):
        make_result(self.student, self.course)
        with self.assertRaises(Exception):
            make_result(self.student, self.course)

    def test_cascade_delete_student(self):
        make_result(self.student, self.course)
        self.student.delete()
        self.assertEqual(Result.objects.count(), 0)

    def test_cascade_delete_course(self):
        make_result(self.student, self.course)
        self.course.delete()
        self.assertEqual(Result.objects.count(), 0)

    def test_result_related_name(self):
        make_result(self.student, self.course)
        self.assertEqual(self.student.results.count(), 1)


# ---------------------------------------------------------------------------
# RevaluationConfiguration Tests
# ---------------------------------------------------------------------------

class RevaluationConfigurationTest(TestCase):

    def test_is_active_when_window_open(self):
        config = RevaluationConfiguration.objects.create(
            is_window_open=True,
            window_start_date=timezone.now() - timedelta(days=1),
            window_end_date=timezone.now() + timedelta(days=1),
        )
        self.assertTrue(config.is_active())

    def test_is_not_active_when_window_closed(self):
        config = RevaluationConfiguration.objects.create(is_window_open=False)
        self.assertFalse(config.is_active())

    def test_is_not_active_before_start(self):
        config = RevaluationConfiguration.objects.create(
            is_window_open=True,
            window_start_date=timezone.now() + timedelta(days=1),
        )
        self.assertFalse(config.is_active())

    def test_is_not_active_after_end(self):
        config = RevaluationConfiguration.objects.create(
            is_window_open=True,
            window_end_date=timezone.now() - timedelta(days=1),
        )
        self.assertFalse(config.is_active())

    def test_str_shows_status(self):
        config = RevaluationConfiguration.objects.create(is_window_open=True)
        self.assertIn("Open", str(config))

        config.is_window_open = False
        config.save()
        self.assertIn("Closed", str(config))


# ---------------------------------------------------------------------------
# RevaluationRequest Tests
# ---------------------------------------------------------------------------

class RevaluationRequestTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.course = make_course()
        self.result = make_result(self.student, self.course, marks=40.00)
        self.admin = User.objects.create_user("admin", password="pass")

    def _make_reval_request(self, order_id="order_001"):
        return RevaluationRequest.objects.create(
            student=self.student,
            result=self.result,
            razorpay_order_id=order_id,
            amount_paid=Decimal("500.00"),
            original_marks=Decimal("40.00"),
            status="PENDING",
        )

    def test_create_request(self):
        req = self._make_reval_request()
        self.assertEqual(req.status, "PENDING")
        self.assertEqual(req.original_marks, Decimal("40.00"))

    def test_str(self):
        req = self._make_reval_request()
        self.assertIn("1RV21CS001", str(req))
        self.assertIn("PENDING", str(req))

    def test_unique_student_result(self):
        self._make_reval_request()
        with self.assertRaises(Exception):
            self._make_reval_request(order_id="order_002")

    def test_unique_razorpay_order_id(self):
        self._make_reval_request("order_001")
        result2 = Result.objects.create(
            student=make_student("1RV21CS002", "Another"),
            course=self.course,
            final_cie_marks=Decimal("50.00"),
            semester=3,
        )
        with self.assertRaises(Exception):
            RevaluationRequest.objects.create(
                student=make_student("1RV21CS002", "Another"),
                result=result2,
                razorpay_order_id="order_001",  # duplicate
                amount_paid=Decimal("500.00"),
                original_marks=Decimal("50.00"),
            )

    def test_default_status_is_pending(self):
        req = self._make_reval_request()
        self.assertEqual(req.status, "PENDING")


# ---------------------------------------------------------------------------
# PaperSeeingConfiguration Tests
# ---------------------------------------------------------------------------

class PaperSeeingConfigurationTest(TestCase):

    def test_is_active(self):
        config = PaperSeeingConfiguration.objects.create(
            is_window_open=True,
            window_start_date=timezone.now() - timedelta(hours=1),
            window_end_date=timezone.now() + timedelta(hours=1),
        )
        self.assertTrue(config.is_active())

    def test_not_active_when_closed(self):
        config = PaperSeeingConfiguration.objects.create(is_window_open=False)
        self.assertFalse(config.is_active())

    def test_default_fee(self):
        config = PaperSeeingConfiguration.objects.create(is_window_open=False)
        self.assertEqual(config.fee_per_subject, Decimal("1000.00"))


# ---------------------------------------------------------------------------
# MakeupExamConfiguration Tests
# ---------------------------------------------------------------------------

class MakeupExamConfigurationTest(TestCase):

    def test_is_active(self):
        config = MakeupExamConfiguration.objects.create(
            is_registration_open=True,
            registration_start_date=timezone.now() - timedelta(days=1),
            registration_end_date=timezone.now() + timedelta(days=1),
        )
        self.assertTrue(config.is_active())

    def test_not_active_when_closed(self):
        config = MakeupExamConfiguration.objects.create(is_registration_open=False)
        self.assertFalse(config.is_active())


# ---------------------------------------------------------------------------
# MakeupExamRequest Tests
# ---------------------------------------------------------------------------

class MakeupExamRequestTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.course1 = make_course("CS301", "DS", semester=3)
        self.course2 = make_course("CS302", "Algo", semester=3)
        MakeupExamConfiguration.objects.create(
            is_registration_open=True,
            fee_per_subject=Decimal("1000.00"),
        )

    def _make_makeup_request(self, exam_cycle="2024-MAKEUP-1", order_id="order_001"):
        req = MakeupExamRequest.objects.create(
            student=self.student,
            semester=3,
            exam_cycle=exam_cycle,
            razorpay_order_id=order_id,
            amount_paid=Decimal("2000.00"),
            status="PAID",
        )
        req.subjects.set([self.course1, self.course2])
        return req

    def test_create_request(self):
        req = self._make_makeup_request()
        self.assertEqual(req.get_subject_count(), 2)

    def test_calculate_total_fee(self):
        req = self._make_makeup_request()
        self.assertEqual(req.calculate_total_fee(), Decimal("2000.00"))

    def test_can_generate_hall_ticket_false_when_pending(self):
        req = self._make_makeup_request()
        self.assertFalse(req.can_generate_hall_ticket())

    def test_can_generate_hall_ticket_true_when_approved(self):
        req = self._make_makeup_request()
        req.status = "APPROVED"
        req.admin_verified = True
        req.proctor_verified = True
        req.razorpay_payment_id = "pay_123"
        req.save()
        self.assertTrue(req.can_generate_hall_ticket())

    def test_unique_student_exam_cycle(self):
        self._make_makeup_request()
        with self.assertRaises(Exception):
            self._make_makeup_request(order_id="order_002")  # same exam_cycle

    def test_str(self):
        req = self._make_makeup_request()
        self.assertIn("1RV21CS001", str(req))
        self.assertIn("2024-MAKEUP-1", str(req))


# ---------------------------------------------------------------------------
# StudentNotification Tests
# ---------------------------------------------------------------------------

class StudentNotificationTest(TestCase):

    def setUp(self):
        self.student = make_student()

    def test_create_notification(self):
        notif = StudentNotification.objects.create(
            student=self.student,
            notification_type="PAYMENT_SUCCESS",
            title="Payment Done",
            message="Your payment was successful.",
        )
        self.assertFalse(notif.is_read)

    def test_mark_as_read(self):
        notif = StudentNotification.objects.create(
            student=self.student,
            notification_type="HALL_TICKET_READY",
            title="Hall Ticket",
            message="Your hall ticket is ready.",
        )
        notif.is_read = True
        notif.save()
        self.assertTrue(StudentNotification.objects.get(pk=notif.pk).is_read)

    def test_cascade_delete_with_student(self):
        StudentNotification.objects.create(
            student=self.student,
            notification_type="REQUEST_SUBMITTED",
            title="Submitted",
            message="Request submitted.",
        )
        self.student.delete()
        self.assertEqual(StudentNotification.objects.count(), 0)


# ---------------------------------------------------------------------------
# AuditLog Tests
# ---------------------------------------------------------------------------

class AuditLogTest(TestCase):

    def setUp(self):
        self.student = make_student()
        self.user = User.objects.create_user("auditor", password="pass")

    def test_create_audit_log(self):
        log = AuditLog.objects.create(
            user=self.user,
            student=self.student,
            action_type="REVALUATION_CREATED",
            description="Student requested revaluation.",
            metadata={"course": "CS301"},
        )
        self.assertEqual(log.action_type, "REVALUATION_CREATED")
        self.assertEqual(log.metadata["course"], "CS301")

    def test_str(self):
        log = AuditLog.objects.create(
            action_type="MAKEUP_PAID",
            description="Payment completed.",
        )
        self.assertIn("MAKEUP_PAID", str(log))

    def test_student_set_null_on_delete(self):
        log = AuditLog.objects.create(
            student=self.student,
            action_type="ADMIN_VERIFIED",
            description="Verified.",
        )
        self.student.delete()
        log.refresh_from_db()
        self.assertIsNone(log.student)


# ---------------------------------------------------------------------------
# UploadHistory Tests
# ---------------------------------------------------------------------------

class UploadHistoryTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("uploader", password="pass")

    def test_create_upload_history(self):
        history = UploadHistory.objects.create(
            upload_type="RESULTS",
            file_name="results_sem3.xlsx",
            uploaded_by=self.user,
            records_processed=100,
            records_created=80,
            records_updated=15,
            records_skipped=5,
        )
        self.assertTrue(history.success)
        self.assertEqual(history.records_processed, 100)

    def test_str(self):
        history = UploadHistory.objects.create(
            upload_type="METADATA",
            file_name="metadata.xlsx",
            uploaded_by=self.user,
        )
        self.assertIn("METADATA", str(history))
        self.assertIn("metadata.xlsx", str(history))

    def test_ordering_latest_first(self):
        UploadHistory.objects.create(upload_type="RESULTS", file_name="first.xlsx", uploaded_by=self.user)
        UploadHistory.objects.create(upload_type="RESULTS", file_name="second.xlsx", uploaded_by=self.user)
        latest = UploadHistory.objects.first()
        self.assertEqual(latest.file_name, "second.xlsx")