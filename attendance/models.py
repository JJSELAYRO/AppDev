from django.db import models
from accounts.models import Student, Teacher, ClassGroup


class QRSession(models.Model):
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='qr_sessions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='created_sessions')
    qr_value = models.CharField(max_length=255, unique=True)
    qr_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"QR Session for {self.class_group} - Active: {self.is_active}"
    
    class Meta:
        verbose_name = 'QR Session'
        verbose_name_plural = 'QR Sessions'
        ordering = ['-created_at']


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    session = models.ForeignKey(QRSession, on_delete=models.CASCADE, related_name='attendances')
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='class_attendances')
    date = models.DateField(auto_now_add=True)
    time_in = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    
    # GPS Data
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    distance_from_school = models.IntegerField(null=True, blank=True, help_text='Distance in meters')
    
    # QR validation
    qr_scanned_at = models.DateTimeField(auto_now_add=True)
    
    # SMS notification
    sms_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        unique_together = ['student', 'session', 'date']
        ordering = ['-date', '-time_in']
    
    def __str__(self):
        return f"{self.student} - {self.status} on {self.date}"


class SMSLog(models.Model):
    parent = models.ForeignKey('accounts.Parent', on_delete=models.CASCADE, related_name='sms_logs')
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='sms_logs')
    message = models.TextField()
    status = models.CharField(max_length=50, default='sent')
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"SMS to {self.parent} - {self.timestamp}"
