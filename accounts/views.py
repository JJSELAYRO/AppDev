from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user must change password
            try:
                if user.profile.must_change_password:
                    messages.warning(request, 'Please change your default password for security.')
                    return redirect('change_password')
            except UserProfile.DoesNotExist:
                pass
            
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            
            # Redirect based on role
            try:
                profile = user.profile
                if profile.role == 'admin':
                    return redirect('admin_dashboard')
                elif profile.role == 'teacher':
                    return redirect('teacher_dashboard')
                elif profile.role == 'student':
                    return redirect('student_dashboard')
                elif profile.role == 'parent':
                    return redirect('parent_dashboard')
            except UserProfile.DoesNotExist:
                pass
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login_new.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def change_password(request):
    """View for users to change password on first login or anytime"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')
        
        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('change_password')
        
        user = request.user
        
        # Verify current password
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Update profile
        user.profile.must_change_password = False
        user.profile.save()
        
        # Re-authenticate user with new password
        from django.contrib.auth import authenticate, login
        user = authenticate(username=user.username, password=new_password)
        if user:
            login(request, user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('dashboard')
    
    # Check if user must change password
    try:
        force_change = request.user.profile.must_change_password
    except:
        force_change = False
    
    return render(request, 'accounts/change_password.html', {'force_change': force_change})
