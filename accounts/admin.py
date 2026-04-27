from django.contrib import admin
from .models import UserProfile, Teacher, Parent, ClassGroup, Student


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone_number']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'employee_id', 'department']
    search_fields = ['user_profile__user__first_name', 'user_profile__user__last_name', 'employee_id']


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'contact_number']
    search_fields = ['user_profile__user__first_name', 'user_profile__user__last_name', 'contact_number']


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'adviser', 'created_at']
    search_fields = ['name', 'section']
    list_filter = ['adviser']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'student_id', 'class_group', 'parent']
    search_fields = ['user_profile__user__first_name', 'user_profile__user__last_name', 'student_id']
    list_filter = ['class_group']
