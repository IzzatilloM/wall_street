import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_instructors(apps, schema_editor):
    """
    Mavjud teacher/admin foydalanuvchilar uchun Instructor
    profillarini yaratadi (avval ko'rinmay qolganlar).
    """
    Instructor = apps.get_model('instructors', 'Instructor')
    User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0],
                          settings.AUTH_USER_MODEL.split('.')[1])

    for user in User.objects.filter(role__in=['teacher', 'admin']):
        if Instructor.objects.filter(user_id=user.pk).exists():
            continue
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        Instructor.objects.create(user_id=user.pk, full_name=full_name)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('instructors', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1) Instructor.user FK ni loyihaning yagona user modeliga yo'naltiramiz
        migrations.AlterField(
            model_name='instructor',
            name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='instructor_profile',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # 2) Ortiqcha (ishlatilmaydigan) instructors.CustomUser modelini o'chiramiz
        migrations.RemoveField(model_name='customuser', name='groups'),
        migrations.RemoveField(model_name='customuser', name='user_permissions'),
        migrations.DeleteModel(name='CustomUser'),
        # 3) Mavjud teacher/admin larni instructorlarga ko'chiramiz
        migrations.RunPython(backfill_instructors, noop),
    ]
