from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from .models import Attendance, Student, Course


class AttendanceModelTest(TestCase):
    """Test cases for Attendance model"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.teacher_user.role = 'teacher'
        self.teacher_user.save()

        self.student_user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )

        # Create course
        self.course = Course.objects.create(
            name='Python Programming',
            code='PYTHON101',
            instructor=self.teacher_user
        )

        # Create student
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='STU001'
        )
        self.student.courses.add(self.course)

    def test_attendance_creation(self):
        """Test creating an attendance record"""
        attendance = Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=timezone.now().date(),
            status='present',
            marked_by=self.teacher_user
        )

        self.assertEqual(attendance.status, 'present')
        self.assertEqual(attendance.student.student_id, 'STU001')

    def test_attendance_unique_together(self):
        """Test unique_together constraint for attendance"""
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=timezone.now().date(),
            status='present',
            marked_by=self.teacher_user
        )

        # Try to create duplicate
        with self.assertRaises(Exception):
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=timezone.now().date(),
                status='absent',
                marked_by=self.teacher_user
            )

    def test_course_attendance_percentage(self):
        """Test course attendance percentage calculation"""
        # Create 10 attendance records
        for i in range(10):
            status = 'present' if i < 7 else 'absent'
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=timezone.now().date() - timezone.timedelta(days=i),
                status=status,
                marked_by=self.teacher_user
            )

        # Get last attendance record
        attendance = Attendance.objects.filter(
            student=self.student,
            course=self.course
        ).last()

        # 7 present out of 10 = 70%
        self.assertEqual(attendance.course_attendance_percent, 70.0)

    def test_get_student_course_attendance(self):
        """Test static method for getting student course attendance"""
        for i in range(5):
            status = 'present' if i < 3 else 'absent'
            Attendance.objects.create(
                student=self.student,
                course=self.course,
                date=timezone.now().date() - timezone.timedelta(days=i),
                status=status,
                marked_by=self.teacher_user
            )

        percentage = Attendance.get_student_course_attendance(self.student, self.course)
        self.assertEqual(percentage, 60.0)  # 3 present out of 5

    def test_get_course_attendance_stats(self):
        """Test course attendance statistics"""
        # Create multiple students and attendance records
        student2_user = User.objects.create_user(
            username='student2',
            password='testpass123'
        )
        student2 = Student.objects.create(
            user=student2_user,
            student_id='STU002'
        )
        student2.courses.add(self.course)

        today = timezone.now().date()

        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=today,
            status='present',
            marked_by=self.teacher_user
        )

        Attendance.objects.create(
            student=student2,
            course=self.course,
            date=today,
            status='absent',
            marked_by=self.teacher_user
        )

        stats = Attendance.get_course_attendance_stats(self.course, today)

        self.assertEqual(stats['total_students'], 2)
        self.assertEqual(stats['present'], 1)
        self.assertEqual(stats['absent'], 1)

    def test_get_student_overall_attendance(self):
        """Test student overall attendance statistics"""
        # Create another course
        course2 = Course.objects.create(
            name='JavaScript',
            code='JS101',
            instructor=self.teacher_user
        )
        self.student.courses.add(course2)

        # Create attendance records for both courses
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=timezone.now().date(),
            status='present',
            marked_by=self.teacher_user
        )

        Attendance.objects.create(
            student=self.student,
            course=course2,
            date=timezone.now().date(),
            status='absent',
            marked_by=self.teacher_user
        )

        stats = Attendance.get_student_overall_attendance(self.student)

        self.assertEqual(stats['total_classes'], 2)
        self.assertEqual(stats['attended'], 1)
        self.assertEqual(stats['absent'], 1)


class AttendanceViewTest(TestCase):
    """Test cases for attendance views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create teacher user
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123'
        )
        self.teacher.role = 'teacher'
        self.teacher.save()

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin.role = 'admin'
        self.admin.is_staff = True
        self.admin.save()

        # Create course
        self.course = Course.objects.create(
            name='Test Course',
            code='TEST101',
            instructor=self.teacher
        )

    def test_attendance_list_view_login_required(self):
        """Test that attendance list view requires login"""
        response = self.client.get(reverse('attendance_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_attendance_list_view_teacher_access(self):
        """Test that teacher can access attendance list"""
        self.client.login(username='teacher1', password='testpass123')
        response = self.client.get(reverse('attendance_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('courses', response.context)

    def test_mark_attendance_post(self):
        """Test marking attendance via POST"""
        # Create student
        student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )
        student = Student.objects.create(
            user=student_user,
            student_id='STU001'
        )
        student.courses.add(self.course)

        self.client.login(username='teacher1', password='testpass123')

        response = self.client.post(reverse('mark_attendance'), {
            'student': student.id,
            'course': self.course.id,
            'date': timezone.now().date(),
            'status': 'present',
            'note': 'Test'
        })

        # Check that attendance was created
        self.assertEqual(
            Attendance.objects.filter(student=student, course=self.course).count(),
            1
        )


class StudentModelTest(TestCase):
    """Test cases for Student model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def test_student_creation(self):
        """Test creating a student"""
        student = Student.objects.create(
            user=self.user,
            student_id='STU001'
        )

        self.assertEqual(student.student_id, 'STU001')
        self.assertEqual(student.get_full_name(), 'John Doe')

    def test_student_unique_id(self):
        """Test that student ID is unique"""
        Student.objects.create(
            user=self.user,
            student_id='STU001'
        )

        another_user = User.objects.create_user(
            username='student2',
            password='testpass123'
        )

        with self.assertRaises(Exception):
            Student.objects.create(
                user=another_user,
                student_id='STU001'
            )


class CourseModelTest(TestCase):
    """Test cases for Course model"""

    def setUp(self):
        """Set up test data"""
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            first_name='John',
            last_name='Instructor'
        )

    def test_course_creation(self):
        """Test creating a course"""
        course = Course.objects.create(
            name='Python Programming',
            code='PYTHON101',
            instructor=self.teacher
        )

        self.assertEqual(course.code, 'PYTHON101')
        self.assertEqual(course.instructor, self.teacher)

    def test_course_unique_code(self):
        """Test that course code is unique"""
        Course.objects.create(
            name='Python Programming',
            code='PYTHON101',
            instructor=self.teacher
        )

        with self.assertRaises(Exception):
            Course.objects.create(
                name='Python Advanced',
                code='PYTHON101',
                instructor=self.teacher
            )