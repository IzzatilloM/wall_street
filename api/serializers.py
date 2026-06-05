from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import CustomUser
from students.models import Student
from payments.models import Payment
from news.models import News
from enrollments.models import Enrollment
from attendance.models import CoinAward


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token ichiga foydalanuvchi roli va ismini qo'shamiz."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        token['full_name'] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'role': user.role,
            'is_verified': user.is_verified,
        }
        return data


class CourseMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    level = serializers.CharField(source='get_level_display')


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            'id', 'first_name', 'last_name', 'full_name',
            'phone', 'parent_phone', 'email', 'gender',
            'birth_date', 'address', 'coins', 'is_active',
            'avatar', 'created_at',
        )

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class StudentUpdateSerializer(serializers.ModelSerializer):
    """Student o'z profilidagi cheklangan maydonlarni tahrirlaydi."""

    class Meta:
        model = Student
        fields = ('phone', 'parent_phone', 'email', 'address', 'image')


class MyCourseSerializer(serializers.ModelSerializer):
    """Studentning yozilgan kurslari (Enrollment asosida) — mobil ilova uchun."""
    course_title    = serializers.CharField(source='course.title', read_only=True)
    category        = serializers.CharField(source='course.category_badge', read_only=True)
    level           = serializers.CharField(source='course.get_level_display', read_only=True)
    duration        = serializers.CharField(source='course.duration_display', read_only=True)
    teacher         = serializers.SerializerMethodField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    payment_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    net_fee         = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining       = serializers.DecimalField(source='remaining_amount', max_digits=12, decimal_places=2, read_only=True)
    payment_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            'id', 'course_title', 'category', 'level', 'duration', 'teacher',
            'status', 'status_display', 'payment_status', 'payment_display',
            'course_fee', 'discount', 'paid_amount', 'net_fee', 'remaining',
            'payment_percent', 'start_date', 'end_date', 'enrolled_at',
        )

    def get_teacher(self, obj):
        if obj.instructor:
            return obj.instructor.full_name
        if obj.course and obj.course.teacher:
            return obj.course.teacher.full_name
        return None


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    month_display = serializers.CharField(source='get_payment_month_display', read_only=True)
    net_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'receipt_number', 'course_title', 'amount', 'discount',
            'net_amount', 'payment_month', 'month_display', 'payment_year',
            'payment_method', 'method_display', 'status', 'status_display',
            'note', 'paid_at',
        )


class CoinAwardSerializer(serializers.ModelSerializer):
    """Talabaga berilgan/ayirilgan coin tarixi — mobil ilova uchun."""
    awarded_by = serializers.SerializerMethodField()

    class Meta:
        model = CoinAward
        fields = ('id', 'amount', 'reason', 'awarded_by', 'created_at')

    def get_awarded_by(self, obj):
        if obj.awarded_by:
            return obj.awarded_by.get_full_name() or obj.awarded_by.username
        return None


class NewsSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = (
            'id', 'title', 'short_text', 'body', 'image',
            'telegram_url', 'is_pinned', 'created_at',
        )

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None
