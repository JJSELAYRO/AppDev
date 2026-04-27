#!/usr/bin/env python
"""
Setup script to create demo data for the QR Attendance System.
Run this in Django shell: python manage.py shell < setup_data.py
"""

from django.contrib.auth.models import User
from accounts.models import UserProfile, Teacher, Parent, Student, ClassGroup
from attendance.models import QRSession, Attendance, SMSLog
from datetime import datetime, timedelta
from django.utils import timezone

print("Creating demo data for QR Attendance System...")

# Create Admin User
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@school.edu',
        'first_name': 'System',
        'last_name': 'Administrator',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin_user.set_password('password123')
    admin_user.save()
    admin_user.profile.role = 'admin'
    admin_user.profile.save()
    print(f"Created admin user: {admin_user.username}")
else:
    print(f"Admin user already exists: {admin_user.username}")

# Create Class Group
class_group, created = ClassGroup.objects.get_or_create(
    name='Grade 10 - Science',
    section='A',
    defaults={
        'adviser': None
    }
)
if created:
    print(f"Created class: {class_group}")
else:
    print(f"Class already exists: {class_group}")

# Create Teacher
teacher_user, created = User.objects.get_or_create(
    username='teacher1',
    defaults={
        'email': 'teacher@school.edu',
        'first_name': 'Maria',
        'last_name': 'Santos',
        'is_staff': True
    }
)
if created:
    teacher_user.set_password('password123')
    teacher_user.save()
    teacher_user.profile.role = 'teacher'
    teacher_user.profile.save()
    
    teacher = Teacher.objects.create(
        user_profile=teacher_user.profile,
        employee_id='TCH001',
        department='Science'
    )
    print(f"Created teacher: {teacher_user.get_full_name()}")
else:
    teacher = Teacher.objects.get(user_profile=teacher_user.profile)
    print(f"Teacher already exists: {teacher_user.get_full_name()}")

# Update class adviser
class_group.adviser = teacher
class_group.save()

# Create Parent
parent_user, created = User.objects.get_or_create(
    username='parent1',
    defaults={
        'email': 'parent@email.com',
        'first_name': 'Juan',
        'last_name': 'Dela Cruz'
    }
)
if created:
    parent_user.set_password('password123')
    parent_user.save()
    parent_user.profile.role = 'parent'
    parent_user.profile.save()
    
    parent = Parent.objects.create(
        user_profile=parent_user.profile,
        contact_number='+639123456789'
    )
    print(f"Created parent: {parent_user.get_full_name()}")
else:
    parent = Parent.objects.get(user_profile=parent_user.profile)
    print(f"Parent already exists: {parent_user.get_full_name()}")

# Create Student
student_user, created = User.objects.get_or_create(
    username='student1',
    defaults={
        'email': 'student@school.edu',
        'first_name': 'Jose',
        'last_name': 'Dela Cruz'
    }
)
if created:
    student_user.set_password('password123')
    student_user.save()
    student_user.profile.role = 'student'
    student_user.profile.save()
    
    student = Student.objects.create(
        user_profile=student_user.profile,
        student_id='STU2024001',
        class_group=class_group,
        parent=parent
    )
    print(f"Created student: {student_user.get_full_name()}")
else:
    student = Student.objects.get(user_profile=student_user.profile)
    print(f"Student already exists: {student_user.get_full_name()}")

# Create additional sample students
for i in range(2, 6):
    student_username = f'student{i}'
    student_user, created = User.objects.get_or_create(
        username=student_username,
        defaults={
            'email': f'student{i}@school.edu',
            'first_name': f'Student{i}',
            'last_name': 'Sample'
        }
    )
    if created:
        student_user.set_password('password123')
        student_user.save()
        student_user.profile.role = 'student'
        student_user.profile.save()
        
        Student.objects.create(
            user_profile=student_user.profile,
            student_id=f'STU202400{i}',
            class_group=class_group,
            parent=parent
        )
        print(f"Created student: {student_user.username}")

# Create sample QR Session
qr_session, created = QRSession.objects.get_or_create(
    qr_value='sample-qr-session-demo',
    defaults={
        'class_group': class_group,
        'teacher': teacher,
        'is_active': False,
        'expires_at': timezone.now() + timedelta(hours=2)
    }
)
if created:
    print(f"Created sample QR session")

print("\n" + "="*50)
print("Demo data setup complete!")
print("="*50)
print("\nLogin credentials:")
print("- Admin:     admin / password123")
print("- Teacher:   teacher1 / password123")
print("- Student:   student1 / password123")
print("- Parent:    parent1 / password123")
print("\nYou can now log in and test the system.")
