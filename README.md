# Mobile QR Code Attendance System with GPS Verification and SMS Notification

A modern, mobile-first web application for schools to track student attendance using QR code scanning, GPS location validation, and SMS notifications to parents.

## Features

### Core Features
- **QR Code Attendance**: Teachers generate QR codes for classes; students scan to mark attendance
- **GPS Validation**: System verifies students are within 100 meters of school
- **SMS Notifications**: Automatic SMS sent to parents when student checks in (via Twilio)
- **Role-Based Access**: Separate dashboards for Admin, Teacher, Student, and Parent
- **Mobile-First Design**: Responsive Bootstrap 5 UI optimized for smartphones

### User Roles
1. **Admin**: Manage users, view system reports
2. **Teacher**: Create QR sessions, view live attendance
3. **Student**: Scan QR codes, view attendance history
4. **Parent**: Receive SMS notifications, view children's attendance

## Technology Stack

### Backend
- **Django** (Python) - Web framework
- **Gunicorn** - WSGI HTTP Server
- **Whitenoise** - Static file serving

### Frontend
- **HTML5/CSS3/JavaScript (ES6)**
- **Bootstrap 5** - UI framework
- **html5-qrcode** - QR code scanner

### Database
- **SQLite** (Development)
- **PostgreSQL** (Production on Render)

### APIs & Services
- **Twilio SMS API** - SMS notifications (trial mode)
- **Browser Geolocation API** - GPS coordinates
- **qrcode library** - QR code generation

## Installation & Setup

### Prerequisites
- Python 3.11+
- pip
- (Optional) PostgreSQL for production

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd attendance_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser and sample data**
   ```bash
   python manage.py shell
   ```
   
   Then run the setup script:
   ```python
   exec(open('setup_data.py').read())
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - URL: http://localhost:8000
   - Admin: http://localhost:8000/admin/

### Demo Accounts
After running setup, these accounts are available:
- **Admin**: `admin` / `password123`
- **Teacher**: `teacher1` / `password123`
- **Student**: `student1` / `password123`
- **Parent**: `parent1` / `password123`

## Deployment on Render

### 1. Create Render Account
Sign up at [render.com](https://render.com)

### 2. Create PostgreSQL Database
- Go to Dashboard → New → PostgreSQL
- Name: `attendance-db`
- Copy the internal database URL

### 3. Create Web Service
- Go to Dashboard → New → Web Service
- Connect your GitHub repository
- Configure:
  - **Name**: `attendance-system`
  - **Environment**: Python 3
  - **Build Command**: 
    ```bash
    pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
    ```
  - **Start Command**: 
    ```bash
    gunicorn attendance_system.wsgi:application
    ```

### 4. Environment Variables
Add these in Render Dashboard → Environment:

```
SECRET_KEY=your-secure-secret-key-here
DEBUG=False
DATABASE_URL=postgres://... (from step 2)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
SCHOOL_LATITUDE=14.5995
SCHOOL_LONGITUDE=120.9842
GPS_RADIUS_METERS=100
```

### 5. Deploy
Click "Create Web Service" and wait for deployment to complete.

## System Architecture

### Database Schema

```
User (Django built-in)
  └── UserProfile (role, phone)
       ├── Teacher (employee_id, department)
       ├── Parent (contact_number)
       └── Student (student_id, class, parent)

ClassGroup (name, section, adviser)
  └── QRSession (qr_value, is_active, expires_at)
       └── Attendance (student, status, gps, sms_sent)
            └── SMSLog (parent, message, status)
```

### Attendance Flow
1. Teacher creates QR session for a class
2. System generates unique QR code (expires in 2 hours)
3. Student scans QR with mobile camera
4. System captures GPS location
5. Backend validates:
   - QR code is valid and active
   - GPS is within 100m radius
   - No duplicate attendance today
6. Attendance marked with status (Present/Late)
7. SMS sent to parent via Twilio
8. Teacher dashboard updates in real-time

### Security Features
- CSRF protection enabled
- Authentication required for all actions
- Server-side validation for QR and GPS
- No hardcoded secrets (use environment variables)
- Secure password hashing

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `GET /accounts/logout/` - User logout

### Dashboard
- `GET /dashboard/` - Redirect to role-based dashboard
- `GET /dashboard/admin/` - Admin dashboard
- `GET /dashboard/teacher/` - Teacher dashboard
- `GET /dashboard/student/` - Student dashboard
- `GET /dashboard/parent/` - Parent dashboard

### QR & Attendance
- `GET /qr/generate/<class_id>/` - Generate QR session (Teacher)
- `GET /qr/view/<session_id>/` - View QR code and attendance
- `GET /qr/scan/` - Student QR scanner page
- `POST /qr/submit/` - Submit attendance with GPS data

## SMS Notification Format

```
Your child [Student Name] is PRESENT at [Time].
(Sent from Twilio trial account)
```

## GPS Validation

- **School Coordinates**: Configurable (default: Manila area)
- **Valid Radius**: 100 meters (configurable)
- **Distance Calculation**: Haversine formula

## File Structure

```
attendance_system/
├── attendance_system/          # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                    # User management
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── attendance/                  # Attendance models
│   ├── models.py
│   └── admin.py
├── qr_module/                 # QR generation & scanning
│   ├── views.py
│   └── urls.py
├── dashboard/                 # Dashboard views
│   ├── views.py
│   └── urls.py
├── core/                      # Core utilities
├── templates/                 # HTML templates
│   ├── base.html
│   ├── accounts/
│   ├── dashboard/
│   └── qr_module/
├── static/                    # CSS, JS, images
│   ├── css/
│   └── js/
├── media/                     # Uploaded files
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── manage.py
└── README.md
```

## Troubleshooting

### QR Scanner Not Working
- Ensure camera permissions are granted
- Use HTTPS in production (required for camera access)
- Try manual QR code entry as fallback

### GPS Not Working
- Allow location access in browser
- Ensure device GPS is enabled
- Refresh GPS by clicking "Refresh" button
- Check if within valid school radius

### SMS Not Sending
- Verify Twilio credentials in environment variables
- Ensure Twilio trial account has verified phone numbers
- Check Twilio console for delivery status

### Deployment Issues
- Verify `DATABASE_URL` is set correctly
- Run `python manage.py collectstatic` manually if static files fail
- Check Render logs for detailed error messages

## License

This project is for educational purposes. Feel free to modify and use as needed.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Render logs for deployment issues
3. Verify all environment variables are set correctly

---

**Built with Django & Bootstrap 5**
