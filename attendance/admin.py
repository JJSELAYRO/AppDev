from django.contrib import admin
from .models import QRSession, Attendance, SMSLog


@admin.register(QRSession)
class QRSessionAdmin(admin.ModelAdmin):
    list_display = ['class_group', 'teacher', 'qr_value', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['class_group__name', 'qr_value']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_group', 'date', 'time_in', 'status', 'sms_sent', 'distance_from_school']
    list_filter = ['status', 'sms_sent', 'date', 'class_group']
    search_fields = ['student__user_profile__user__first_name', 'student__user_profile__user__last_name', 'student__student_id']
    date_hierarchy = 'date'


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['parent', 'attendance', 'status', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['parent__user_profile__user__first_name', 'parent__user_profile__user__last_name']
