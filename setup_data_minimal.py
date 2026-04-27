#!/usr/bin/env python
"""
Setup script - Creates only admin user for fresh system setup.
Run: python manage.py shell < setup_data_minimal.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

print("=" * 50)
print("QR Attendance System - Initial Setup")
print("=" * 50)

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
    admin_user.set_password('admin123')
    admin_user.save()
    # Update profile role
    admin_user.profile.role = 'admin'
    admin_user.profile.save()
    print(f"✓ Created admin user: admin")
else:
    admin_user.set_password('admin123')
    admin_user.save()
    admin_user.profile.role = 'admin'
    admin_user.profile.save()
    print(f"✓ Reset admin password: admin")

print("=" * 50)
print("Setup complete!")
print("=" * 50)
print("Login credentials:")
print("  Username: admin")
print("  Password: admin123")
print("=" * 50)
