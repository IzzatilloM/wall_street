from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Attendance Management System'

    def ready(self):
        """
        Import signals when app is ready
        """
        try:
            import attendance.signals
        except ImportError:
            pass