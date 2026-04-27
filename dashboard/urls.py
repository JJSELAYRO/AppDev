from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('parent/', views.parent_dashboard, name='parent_dashboard'),
    # Excel upload/download for admin
    path('admin/upload-students/', views.upload_students_excel, name='upload_students_excel'),
    path('admin/download-template/', views.download_students_template, name='download_students_template'),
    path('admin/download-students/', views.download_all_students, name='download_all_students'),
]
