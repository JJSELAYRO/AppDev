from django.urls import path
from . import views

urlpatterns = [
    path('generate/<int:class_id>/', views.generate_qr_session, name='generate_qr'),
    path('view/<int:session_id>/', views.view_qr_session, name='view_qr'),
    path('scan/', views.scan_qr_page, name='scan_qr'),
    path('submit/', views.submit_attendance, name='submit_attendance'),
    path('api/scan-attendance/', views.api_scan_attendance, name='api_scan_attendance'),
]
