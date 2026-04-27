from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    must_change_password = models.BooleanField(default=False, help_text='Force user to change password on first login')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Teacher(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.employee_id}"
    
    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'


class Parent(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='parent_profile')
    contact_number = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.contact_number}"
    
    class Meta:
        verbose_name = 'Parent'
        verbose_name_plural = 'Parents'


class ClassGroup(models.Model):
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=50, blank=True, null=True)
    adviser = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='advised_classes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} {self.section or ''}"
    
    class Meta:
        verbose_name = 'Class Group'
        verbose_name_plural = 'Class Groups'


class Student(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.student_id}"
    
    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
