from django.db.models import Sum
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from students.models import Student
from payments.models import Payment
from news.models import News
from enrollments.models import Enrollment
from attendance.models import CoinAward, Attendance, Student as AttStudent

from .serializers import (
    MyTokenObtainPairSerializer,
    StudentSerializer,
    StudentUpdateSerializer,
    PaymentSerializer,
    NewsSerializer,
    MyCourseSerializer,
    CoinAwardSerializer,
)


class MyTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/  →  {username, password} bilan JWT olish."""
    serializer_class = MyTokenObtainPairSerializer


def _get_student(user):
    """Foydalanuvchiga bog'langan student profilini qaytaradi (yoki None)."""
    return Student.objects.filter(user=user).first()


class ProfileView(APIView):
    """GET/PATCH /api/me/  →  joriy student profili."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student = _get_student(request.user)
        if not student:
            return Response(
                {'detail': "Sizga student profili biriktirilmagan."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(StudentSerializer(student, context={'request': request}).data)

    def patch(self, request):
        student = _get_student(request.user)
        if not student:
            return Response(
                {'detail': "Sizga student profili biriktirilmagan."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StudentUpdateSerializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentSerializer(student, context={'request': request}).data)


class MyPaymentsView(generics.ListAPIView):
    """GET /api/me/payments/  →  joriy studentning to'lovlari."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        student = _get_student(self.request.user)
        if not student:
            return Payment.objects.none()
        return Payment.objects.filter(student=student).select_related('course')


class MyCoursesView(generics.ListAPIView):
    """GET /api/me/courses/  →  joriy studentning yozilgan kurslari."""
    serializer_class = MyCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        student = _get_student(self.request.user)
        if not student:
            return Enrollment.objects.none()
        return (
            Enrollment.objects.filter(student=student)
            .select_related('course', 'course__teacher', 'instructor')
            .order_by('-enrolled_at')
        )


class MyCoinsView(APIView):
    """GET /api/me/coins/  →  joriy studentning coin balansi + berilish tarixi."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student = _get_student(request.user)
        balance = student.coins if student else 0
        awards = (
            CoinAward.objects
            .filter(student__user=request.user)
            .select_related('awarded_by')
        )
        return Response({
            'balance': balance,
            'awards': CoinAwardSerializer(awards, many=True).data,
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payments_summary(request):
    """GET /api/me/payments/summary/  →  to'lovlar bo'yicha umumiy hisob."""
    student = _get_student(request.user)
    if not student:
        return Response({'total_paid': 0, 'pending': 0, 'count': 0, 'coins': 0})

    qs = Payment.objects.filter(student=student)
    paid = qs.filter(status='paid').aggregate(s=Sum('amount'))['s'] or 0
    pending = qs.filter(status__in=['pending', 'partial', 'overdue']).aggregate(
        s=Sum('amount'))['s'] or 0
    return Response({
        'total_paid': float(paid),
        'pending': float(pending),
        'count': qs.count(),
        'coins': student.coins,
    })


class NewsListView(generics.ListAPIView):
    """GET /api/news/  →  chop etilgan yangiliklar."""
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return News.objects.filter(is_published=True)


class NewsDetailView(generics.RetrieveAPIView):
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]
    queryset = News.objects.filter(is_published=True)


# ═══════════════════════════════════════════════════════════════════════════
#  REYTING (coin bo'yicha) + DARSLAR
# ═══════════════════════════════════════════════════════════════════════════
def _avatar_url(request, student):
    if student and student.image and hasattr(student.image, 'url'):
        url = student.image.url
        return request.build_absolute_uri(url) if request else url
    return None


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_rank(request):
    """GET /api/me/rank/  →  joriy studentning coin bo'yicha o'rni."""
    student = _get_student(request.user)
    if not student:
        return Response({'rank': None, 'total': 0, 'coins': 0, 'percentile': 0})

    total = Student.objects.filter(is_active=True).count()
    coins = student.coins or 0
    # Undan ko'p coinga ega studentlar soni + 1 = o'rin
    higher = Student.objects.filter(is_active=True, coins__gt=coins).count()
    rank = higher + 1
    percentile = round((1 - (rank - 1) / total) * 100) if total else 0
    return Response({
        'rank': rank,
        'total': total,
        'coins': coins,
        'percentile': percentile,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def leaderboard(request):
    """GET /api/leaderboard/  →  eng ko'p coinli top studentlar + mening o'rnim."""
    try:
        limit = min(int(request.GET.get('limit', 50)), 100)
    except (TypeError, ValueError):
        limit = 50

    me = _get_student(request.user)
    top = Student.objects.filter(is_active=True).order_by('-coins', 'id')[:limit]
    rows = []
    for i, s in enumerate(top, start=1):
        rows.append({
            'rank': i,
            'name': s.full_name,
            'coins': s.coins or 0,
            'avatar': _avatar_url(request, s),
            'is_me': bool(me and s.id == me.id),
        })

    # Agar joriy student top ro'yxatda bo'lmasa — uning o'rnini alohida qo'shamiz
    my_rank = None
    if me:
        higher = Student.objects.filter(is_active=True, coins__gt=(me.coins or 0)).count()
        my_rank = higher + 1

    return Response({
        'leaderboard': rows,
        'my_rank': my_rank,
        'total': Student.objects.filter(is_active=True).count(),
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_lessons(request):
    """GET /api/me/lessons/  →  joriy studentning darslari (davomat) + xulosa."""
    ats = AttStudent.objects.filter(user=request.user).first()
    if not ats:
        return Response({
            'lessons': [],
            'summary': {'total_classes': 0, 'attended': 0, 'absent': 0,
                        'late': 0, 'attendance_percent': 0},
            'by_course': [],
        })

    recs = (Attendance.objects.filter(student=ats)
            .select_related('course').order_by('-date')[:100])
    lessons = [{
        'date': str(r.date),
        'course': r.course.name if r.course else '',
        'status': r.status,
        'status_display': r.get_status_display(),
    } for r in recs]

    summary = Attendance.get_student_overall_attendance(ats)

    # Kurslar bo'yicha davomat foizi
    by_course = []
    for course in ats.courses.all():
        stats = Attendance.get_course_attendance_stats(course)
        percent = Attendance.get_student_course_attendance(ats, course)
        total = Attendance.objects.filter(student=ats, course=course).count()
        by_course.append({
            'course': course.name,
            'total': total,
            'attendance_percent': percent,
        })

    return Response({
        'lessons': lessons,
        'summary': summary,
        'by_course': by_course,
    })
