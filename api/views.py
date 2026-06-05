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
from attendance.models import CoinAward

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
