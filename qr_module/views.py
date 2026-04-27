import uuid
import json
import math
import qrcode
import qrcode.image.svg
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from accounts.models import UserProfile, Student, Teacher, ClassGroup
from attendance.models import QRSession, Attendance, SMSLog
from twilio.rest import Client


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two GPS coordinates using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance)


import urllib.parse

def get_sms_notification_data(parent, student_name, attendance_time, latitude, longitude, status='present'):
    """
    Generate SMS notification data for parent.
    For Render deployment: Student's phone will send SMS manually.
    Message is LOCKED/OFFICIAL - student cannot edit.
    """
    
    if not parent or not parent.contact_number:
        return None, "Parent contact number not found"
    
    # Format phone number to +63 format
    phone = parent.contact_number.strip()
    if phone.startswith('0'):
        phone = '+63' + phone[1:]
    elif not phone.startswith('+'):
        phone = '+63' + phone
    
    # Format time (e.g., "8:30 AM")
    time_str = attendance_time.strftime('%I:%M %p')
    
    # Format coordinates (e.g., "14.5995°N, 120.9842°E")
    lat_str = f"{abs(latitude):.4f}°{'N' if latitude >= 0 else 'S'}"
    lng_str = f"{abs(longitude):.4f}°{'E' if longitude >= 0 else 'W'}"
    
    # Google Maps link for exact location
    maps_url = f"https://maps.google.com/?q={latitude},{longitude}"
    
    # Determine status text (PRESENT or LATE)
    status_text = "PRESENT" if status == "present" else "LATE"
    
    # === LOCKED OFFICIAL MESSAGE (Tagalog with Location) ===
    # Student CANNOT edit this message
    message = (
        f"Ang anak ninyong si {student_name} ay {status_text} ngayong {time_str}. "
        f"Lokasyon: {lat_str}, {lng_str}. "
        f"Tingnan sa mapa: {maps_url} "
        f"QR Attendance System"
    )
    
    # Alternative: English version (uncomment if preferred)
    # message = (
    #     f"Your child {student_name} is {status_text} at {time_str}. "
    #     f"Location: {lat_str}, {lng_str}. "
    #     f"View map: {maps_url} "
    #     f"QR Attendance System"
    # )
    
    # URL encode for SMS link
    encoded_message = urllib.parse.quote(message)
    
    # Build SMS data
    sms_data = {
        'phone': phone,
        'phone_display': phone,  # For display purposes
        'message': message,  # LOCKED - official message
        'message_preview': message[:100] + "..." if len(message) > 100 else message,
        'coordinates': f"{lat_str}, {lng_str}",
        'maps_url': maps_url,
        'time': time_str,
        'status': status_text,
        'student_name': student_name,
        'sms_link': f"sms:{phone}?body={encoded_message}",
        'whatsapp_link': f"https://wa.me/{phone.replace('+', '')}?text={encoded_message}",
        'is_locked': True,  # Flag to indicate this is official locked message
        'warning': 'OFFICIAL SCHOOL MESSAGE - DO NOT EDIT'
    }
    
    return sms_data, "SMS data prepared for manual sending"


# Keep old function for backward compatibility if needed
def send_sms_notification(parent, student_name, attendance_time):
    """Legacy function - returns SMS data for student to send manually"""
    sms_data, message = get_sms_notification_data(
        parent, student_name, attendance_time, 
        latitude=0, longitude=0, status='present'
    )
    return sms_data is not None, message


@login_required
def generate_qr_session(request, class_id):
    """Generate a new QR code session for a class"""
    try:
        if request.user.profile.role != 'teacher':
            return JsonResponse({'success': False, 'error': 'Access denied. Teacher only.'})
    except:
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    
    try:
        teacher = request.user.profile.teacher_profile
        class_group = get_object_or_404(ClassGroup, id=class_id)
        
        # Deactivate old sessions for this class
        QRSession.objects.filter(class_group=class_group, is_active=True).update(is_active=False)
        
        # Generate unique QR value
        qr_value = str(uuid.uuid4())
        
        # Create new session (expires in 2 hours)
        session = QRSession.objects.create(
            class_group=class_group,
            teacher=teacher,
            qr_value=qr_value,
            is_active=True,
            expires_at=timezone.now() + timezone.timedelta(hours=2)
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_value)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save QR image
        qr_filename = f"qr_{session.id}_{qr_value[:8]}.png"
        from django.core.files.base import ContentFile
        session.qr_image.save(qr_filename, ContentFile(buffer.read()), save=True)
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'qr_value': qr_value,
            'expires_at': session.expires_at.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def view_qr_session(request, session_id):
    """View QR code for a session"""
    try:
        if request.user.profile.role != 'teacher':
            messages.error(request, 'Access denied. Teacher only.')
            return redirect('dashboard')
    except:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    session = get_object_or_404(QRSession, id=session_id)
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(session.qr_value)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    qr_base64 = buffer.getvalue().hex()
    
    # Get live attendance for this session
    attendances = Attendance.objects.filter(session=session).select_related(
        'student', 'student__user_profile__user'
    ).order_by('-time_in')
    
    context = {
        'session': session,
        'class_group': session.class_group,
        'qr_base64': qr_base64,
        'attendances': attendances,
    }
    return render(request, 'qr_module/view_qr.html', context)


@login_required
def scan_qr_page(request):
    """Page for students to scan QR codes"""
    try:
        if request.user.profile.role != 'student':
            messages.error(request, 'Access denied. Student only.')
            return redirect('dashboard')
    except:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    student = request.user.profile.student_profile
    
    context = {
        'student': student,
        'school_lat': settings.SCHOOL_LATITUDE,
        'school_lng': settings.SCHOOL_LONGITUDE,
        'gps_radius': settings.GPS_RADIUS_METERS,
    }
    return render(request, 'qr_module/scan_qr_mobile.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def submit_attendance(request):
    """Submit attendance after scanning QR code"""
    try:
        data = json.loads(request.body)
        
        qr_value = data.get('qr_value')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not all([qr_value, latitude, longitude]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required data. QR code and GPS location required.'
            })
        
        # Get student
        try:
            student = request.user.profile.student_profile
        except:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found.'
            })
        
        # Validate QR session
        try:
            session = QRSession.objects.get(
                qr_value=qr_value,
                is_active=True,
                expires_at__gt=timezone.now()
            )
        except QRSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired QR code.'
            })
        
        # Validate GPS location
        distance = calculate_distance(
            settings.SCHOOL_LATITUDE,
            settings.SCHOOL_LONGITUDE,
            float(latitude),
            float(longitude)
        )
        
        if distance > settings.GPS_RADIUS_METERS:
            return JsonResponse({
                'success': False,
                'error': f'You are {distance} meters away from school. Must be within {settings.GPS_RADIUS_METERS} meters.'
            })
        
        # Check for duplicate attendance today
        today = timezone.now().date()
        existing_attendance = Attendance.objects.filter(
            student=student,
            session=session,
            date=today
        ).first()
        
        if existing_attendance:
            return JsonResponse({
                'success': False,
                'error': 'You have already recorded attendance for this session today.'
            })
        
        # Determine status (Late if after 8:00 AM)
        current_time = timezone.now().time()
        status = 'present'
        if current_time.hour >= 8 and current_time.minute > 0:
            status = 'late'
        
        # Create attendance record
        attendance = Attendance.objects.create(
            student=student,
            session=session,
            class_group=session.class_group,
            status=status,
            latitude=latitude,
            longitude=longitude,
            distance_from_school=distance,
            sms_sent=False  # Will be True when student sends manually
        )
        
        # Prepare SMS notification data (for student to send manually)
        sms_data = None
        if student.parent:
            sms_data, sms_message = get_sms_notification_data(
                parent=student.parent,
                student_name=student.user_profile.user.get_full_name(),
                attendance_time=attendance.time_in,
                latitude=float(latitude),
                longitude=float(longitude),
                status=status
            )
            
            # Log that SMS data was prepared (student will send manually)
            if sms_data:
                SMSLog.objects.create(
                    parent=student.parent,
                    attendance=attendance,
                    message=sms_data['message'],
                    status='pending',  # Student needs to send manually
                    error_message=None
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance recorded successfully! Status: {status.title()}',
            'status': status,
            'distance': distance,
            'sms_data': sms_data,  # Student uses this to send SMS
            'sms_instructions': 'Tap "Send SMS" button to notify parent'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def api_scan_attendance(request):
    """
    API endpoint for seamless QR scan attendance with GPS validation.
    POST /api/scan-attendance/
    
    Payload:
    {
        "qr_value": "...",
        "latitude": ...,
        "longitude": ...
    }
    
    Response:
    {
        "success": true/false,
        "message": "...",
        "status": "present/late",
        "distance": ...,
        "sms_sent": {...}
    }
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST requests allowed.'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        qr_value = data.get('qr_value')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Validate required fields
        if not qr_value:
            return JsonResponse({
                'success': False,
                'error': 'QR code value is required.'
            })
        
        if not latitude or not longitude:
            return JsonResponse({
                'success': False,
                'error': 'GPS location is required. Please enable location services.'
            })
        
        # Get student profile
        try:
            student = Student.objects.get(user_profile=request.user.profile)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student profile not found.'
            })
        
        # Validate QR Session
        try:
            session = QRSession.objects.get(
                qr_value=qr_value,
                is_active=True,
                expires_at__gt=timezone.now()
            )
        except QRSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired QR code.'
            })
        
        # Validate GPS location
        distance = calculate_distance(
            settings.SCHOOL_LATITUDE,
            settings.SCHOOL_LONGITUDE,
            float(latitude),
            float(longitude)
        )
        
        if distance > settings.GPS_RADIUS_METERS:
            return JsonResponse({
                'success': False,
                'error': f'You are {distance} meters away from school. Must be within {settings.GPS_RADIUS_METERS} meters.'
            })
        
        # Check for duplicate attendance today
        today = timezone.now().date()
        existing_attendance = Attendance.objects.filter(
            student=student,
            session=session,
            date=today
        ).first()
        
        if existing_attendance:
            return JsonResponse({
                'success': False,
                'error': 'You have already recorded attendance for this session today.'
            })
        
        # Determine status (Late if after 8:00 AM)
        current_time = timezone.now().time()
        status = 'present'
        if current_time.hour >= 8 and current_time.minute > 0:
            status = 'late'
        
        # Create attendance record
        attendance = Attendance.objects.create(
            student=student,
            session=session,
            class_group=session.class_group,
            status=status,
            latitude=latitude,
            longitude=longitude,
            distance_from_school=distance,
            sms_sent=False
        )
        
        # Send SMS notification if parent exists
        sms_result = None
        if student.parent:
            success, message = send_sms_notification(
                student.parent,
                student.user_profile.user.get_full_name(),
                attendance.time_in
            )
            
            attendance.sms_sent = success
            attendance.sms_sent_at = timezone.now() if success else None
            attendance.save()
            
            # Log SMS
            SMSLog.objects.create(
                parent=student.parent,
                attendance=attendance,
                message=message if not success else "SMS sent successfully",
                status='sent' if success else 'failed',
                error_message=message if not success else None
            )
            
            sms_result = {
                'sent': success,
                'message': message if not success else "SMS sent to parent"
            }
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance recorded successfully! Status: {status.title()}',
            'status': status,
            'distance': distance,
            'sms_sent': sms_result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
