def user_role(request):
    """Context processor to add user role to template context"""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            return {
                'user_role': profile.role,
                'is_admin': profile.role == 'admin',
                'is_teacher': profile.role == 'teacher',
                'is_student': profile.role == 'student',
                'is_parent': profile.role == 'parent',
            }
        except:
            pass
    return {
        'user_role': None,
        'is_admin': False,
        'is_teacher': False,
        'is_student': False,
        'is_parent': False,
    }
