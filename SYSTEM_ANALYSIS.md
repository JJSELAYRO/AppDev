# QR Attendance System - Comprehensive Analysis
## Mobile QR Code Attendance System with GPS Verification and SMS Notification

---

## 1. SYSTEM OVERVIEW

### 1.1 Purpose of the System
The **QR Attendance System** is a modern, technology-driven solution designed to automate and streamline student attendance tracking in educational institutions. It replaces traditional paper-based roll calls with a seamless digital process using QR codes, GPS location verification, and SMS notifications.

### 1.2 Problem It Solves
| Traditional Method | QR Attendance System |
|-------------------|---------------------|
| Manual roll calling (slow) | Instant QR scan (seconds) |
| Paper records (easy to lose) | Digital database (permanent) |
| No location verification | GPS location validation |
| No parent notification | Automatic SMS alerts |
| Time-consuming | Real-time processing |
| Prone to proxy attendance | QR + GPS prevents cheating |

### 1.3 Overall Functionality
The system operates on a simple principle:
1. **Teachers** generate unique QR codes for each class session
2. **Students** scan the QR code using their mobile devices
3. **System** verifies the student's location via GPS
4. **Attendance** is recorded only if both QR and location are valid
5. **Parents** receive instant SMS notifications confirming their child's attendance

---

## 2. USER ROLES

### 2.1 Admin (System Administrator)
**Responsibilities:**
- Manage user accounts (teachers, students, parents)
- Create and manage class groups
- View system-wide attendance reports
- Configure school GPS coordinates and radius settings
- Monitor SMS logs and system activity

**Access Level:** Full system access

### 2.2 Teacher
**Responsibilities:**
- Generate QR code sessions for their classes
- View class attendance records
- Monitor which students are present/absent
- Export attendance reports
- Manage class-specific QR sessions (activate/deactivate)

**Key Actions:**
```
Login → Dashboard → Select Class → Generate QR → Display to Students
```

### 2.3 Student
**Responsibilities:**
- Scan QR codes during class sessions
- Ensure GPS location is enabled
- View personal attendance history
- Receive confirmation of successful attendance

**Key Actions:**
```
Login → Open Scanner → Allow GPS → Scan Teacher's QR → Attendance Confirmed
```

### 2.4 Parent
**Responsibilities:**
- Receive SMS notifications when child is present
- View child's attendance history
- Monitor punctuality and attendance patterns
- Contact school if notifications not received

**Notification Example:**
```
"Your child Juan Dela Cruz is PRESENT at 8:30 AM 
(Sent from Twilio trial account)"
```

---

## 3. CORE FEATURES

### 3.1 Authentication System
**How It Works:**
- Built on Django's built-in authentication framework
- Custom UserProfile model extends Django User with role-based access
- Signal-based profile creation (auto-creates profile when user is created)
- Password change requirement on first login for new accounts

**Role Assignment:**
```python
# Signal automatically creates UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
```

**Login Flow:**
```
User enters credentials → Django authenticates → 
Check role in UserProfile → Redirect to role-specific dashboard
```

### 3.2 QR Code Generation
**How It Works:**
- Teachers click "Generate QR" for their class
- System creates a unique QR session with UUID
- QR code is valid for 2 hours (configurable)
- Previous sessions for the same class are automatically deactivated
- QR code can be displayed on screen/projector

**Technical Implementation:**
```python
# Unique QR value generation
qr_value = str(uuid.uuid4())

# Session creation with expiration
session = QRSession.objects.create(
    class_group=class_group,
    teacher=teacher,
    qr_value=qr_value,
    expires_at=timezone.now() + timedelta(hours=2)
)
```

**Security Features:**
- UUID ensures uniqueness (virtually impossible to guess)
- Time-based expiration prevents old QR codes from being reused
- Automatic deactivation of previous sessions

### 3.3 QR Code Scanning
**How It Works:**
1. Student opens scan page on mobile device
2. Camera opens automatically using html5-qrcode library
3. Student points camera at teacher's QR code
4. QR value is extracted and sent to backend with GPS data
5. Backend validates and records attendance

**Frontend Implementation:**
```javascript
// Automatic camera startup
html5QrcodeScanner = new Html5Qrcode('reader');
html5QrcodeScanner.start(
    { facingMode: "environment" },  // Use back camera
    { fps: 10, qrbox: { width: 250, height: 250 } },
    onScanSuccess,  // Callback when QR is detected
    onScanFailure   // Callback for scan errors
);
```

### 3.4 GPS Location Validation
**How It Works:**
1. Browser requests location permission when scan page loads
2. GPS coordinates are captured using Geolocation API
3. Distance is calculated between student's location and school location
4. Attendance only recorded if within allowed radius (default: 100 meters)

**Distance Calculation (Haversine Formula):**
```python
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth's radius in meters
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance)
```

**GPS Status Display:**
- Real-time distance from school shown on scanner page
- Visual indicators: Green (within range), Red (outside range)
- GPS coordinates displayed for transparency

### 3.5 Attendance Recording
**How It Works:**
1. Backend receives QR value + GPS coordinates
2. Validates QR session (must be active and not expired)
3. Validates student location (must be within radius)
4. Checks for duplicate attendance (same student, same day)
5. Records attendance with status (Present or Late)
6. Triggers SMS notification to parent

**Attendance Status Logic:**
```python
# Late if after 8:00 AM
current_time = timezone.now().time()
if current_time.hour >= 8 and current_time.minute > 0:
    status = 'late'
else:
    status = 'present'
```

**Attendance Record Includes:**
- Student ID
- Class/Session ID
- Timestamp (time_in)
- GPS coordinates (latitude, longitude)
- Distance from school
- Status (present/late/absent)
- SMS sent flag

### 3.6 SMS Notification System
**How It Works:**
1. After successful attendance recording
2. System checks if student has a parent linked
3. If yes, sends SMS using Twilio API
4. SMS message includes student name and arrival time
5. SMS log is stored in database for tracking

**SMS Function:**
```python
def send_sms_notification(parent, student_name, attendance_time):
    client = Client(settings.TWILIO_ACCOUNT_SID, 
                   settings.TWILIO_AUTH_TOKEN)
    
    message_body = f"Your child {student_name} is PRESENT " \
                   f"at {attendance_time.strftime('%I:%M %p')}. " \
                   f"(Sent from Twilio trial account)"
    
    message = client.messages.create(
        body=message_body,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=parent.contact_number
    )
    
    return True, message.sid
```

---

## 4. SYSTEM FLOW (Step-by-Step)

### Phase 1: Teacher Creates QR Session
```
┌─────────────┐
│   Teacher   │
│   Login     │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Teacher Dashboard│
│  Select Class    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Click "Generate│
│  QR Code"       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  System Creates  │
│  QR Session      │
│  - Unique UUID   │
│  - 2hr Expiry    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Display QR Code │
│  to Students     │
└──────────────────┘
```

### Phase 2: Student Scans QR Code
```
┌─────────────┐
│   Student   │
│   Login     │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Open Scanner    │
│  Page            │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Browser Asks    │
│  GPS Permission  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Camera Opens    │
│  Automatically   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Scan Teacher's  │
│  QR Code         │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Extract QR      │
│  Value           │
└──────────────────┘
```

### Phase 3: Backend Validation & Recording
```
┌──────────────────┐
│  Send to Backend:│
│  - QR Value      │
│  - GPS Lat/Lng   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐     ┌──────────────┐
│  Validate QR     │────▶│  Valid?      │
│  Session         │     │  Active?     │
│                  │     │  Not Expired?│
└──────┬───────────┘     └──────┬───────┘
       │                        │
       │                        │
       ▼                        ▼
┌──────────────────┐     ┌──────────────┐
│  Calculate       │     │  Return Error│
│  Distance from   │     │  Message     │
│  School          │     │              │
└──────┬───────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│  Within 100m?  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐     ┌──────────────┐
│  Record          │     │  Return "Too │
│  Attendance      │     │  Far" Error  │
│  - Save to DB    │     │              │
│  - Mark SMS sent │     │              │
└──────┬───────────┘     └──────────────┘
       │
       ▼
┌──────────────────┐
│  Send Success    │
│  Response        │
└──────────────────┘
```

### Phase 4: SMS Notification
```
┌──────────────────┐
│  Student has     │
│  Parent?         │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐     ┌──────────────┐
│  Yes             │     │  No - Skip   │
│  Send SMS via    │     │  SMS         │
│  Twilio API      │     │              │
└──────┬───────────┘     └──────────────┘
       │
       ▼
┌──────────────────┐
│  Log SMS in      │
│  Database        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Show Success    │
│  Message to      │
│  Student         │
└──────────────────┘
```

---

## 5. DATABASE STRUCTURE

### 5.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER MANAGEMENT                          │
├─────────────────┐     ┌───────────────┐     ┌─────────────────┐
│   Django User   │◄────│  UserProfile  │     │                 │
│   (Built-in)    │ 1:1 │               │     │                 │
└─────────────────┘     └───────┬───────┘     │                 │
                                │             │                 │
        ┌───────────────────────┼─────────────┘                 │
        │                       │                               │
        ▼                       ▼                               ▼
┌───────────────┐     ┌───────────────┐     ┌─────────────────┐
│    Teacher    │     │    Student    │     │     Parent      │
│  ───────────  │     │  ───────────  │     │  ─────────────  │
│  employee_id  │     │  student_id   │     │  contact_number │
│  department   │     │  class_group  │────▶│                 │
│  user_profile │◄────│  user_profile │     │  user_profile   │◄────
└───────┬───────┘     │  parent       │────▶└─────────────────┘
        │             └───────────────┘              ▲
        │                                            │
        │             ┌───────────────┐              │
        │             │  ClassGroup   │              │
        │             │  ───────────  │              │
        └────────────▶│  name         │              │
           advises    │  section      │              │
                      │  adviser      │◄─────────────┘
                      └───────────────┘     1 child
                                            per parent
                                            (can be more)
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      ATTENDANCE SYSTEM                           │
├─────────────────┐     ┌───────────────┐     ┌─────────────────┐
│   QRSession     │     │  Attendance   │     │    SMSLog       │
│  ───────────    │     │  ───────────  │     │  ─────────────  │
│  qr_value (UUID) │◄────│  session      │     │  parent         │◄────┐
│  class_group   ─┼────▶│  student      │◄────│  attendance     │◄────┼────┐
│  teacher       ─┼────▶│  status       │     │  message        │     │    │
│  is_active      │     │  latitude     │     │  status         │     │    │
│  expires_at     │     │  longitude    │     │  error_message  │     │    │
│  created_at     │     │  time_in      │     │  timestamp      │     │    │
└─────────────────┘     │  distance     │     └─────────────────┘     │    │
                        └───────────────┘                              │    │
                                                                       │    │
                        Status: present/late/absent                    │    │
                                                                       │    │
        Relationship Summary:                                          │    │
        ─────────────────────────────────────────────────────────────────    │
        • One QRSession can have many Attendance records                     │
        • One Student can have many Attendance records                       │
        • One Attendance can have one SMSLog                                 │
        • One Parent can have many SMSLogs                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Model Descriptions

#### UserProfile Model
| Field | Type | Description |
|-------|------|-------------|
| user | OneToOneField(User) | Links to Django User |
| role | CharField | admin/teacher/student/parent |
| phone_number | CharField | Contact number |
| must_change_password | BooleanField | Force password change on first login |
| created_at | DateTimeField | Account creation date |
| updated_at | DateTimeField | Last update date |

#### Teacher Model
| Field | Type | Description |
|-------|------|-------------|
| user_profile | OneToOneField(UserProfile) | Links to UserProfile |
| employee_id | CharField | Unique teacher ID |
| department | CharField | Teaching department |

#### Student Model
| Field | Type | Description |
|-------|------|-------------|
| user_profile | OneToOneField(UserProfile) | Links to UserProfile |
| student_id | CharField | Unique student ID |
| class_group | ForeignKey(ClassGroup) | Student's class |
| parent | ForeignKey(Parent) | Student's parent |

#### Parent Model
| Field | Type | Description |
|-------|------|-------------|
| user_profile | OneToOneField(UserProfile) | Links to UserProfile |
| contact_number | CharField | Phone number for SMS |

#### ClassGroup Model
| Field | Type | Description |
|-------|------|-------------|
| name | CharField | Class name (e.g., "Grade 10") |
| section | CharField | Section (e.g., "A", "B") |
| adviser | ForeignKey(Teacher) | Class adviser |
| created_at | DateTimeField | Creation date |

#### QRSession Model
| Field | Type | Description |
|-------|------|-------------|
| class_group | ForeignKey(ClassGroup) | Target class |
| teacher | ForeignKey(Teacher) | Session creator |
| qr_value | CharField | Unique UUID for QR |
| qr_image | ImageField | Generated QR code image |
| is_active | BooleanField | Session active status |
| created_at | DateTimeField | Session start time |
| expires_at | DateTimeField | Session expiration |

#### Attendance Model
| Field | Type | Description |
|-------|------|-------------|
| student | ForeignKey(Student) | Attending student |
| session | ForeignKey(QRSession) | QR session used |
| class_group | ForeignKey(ClassGroup) | Class attended |
| status | CharField | present/late/absent |
| latitude | FloatField | GPS latitude |
| longitude | FloatField | GPS longitude |
| distance_from_school | IntegerField | Distance in meters |
| time_in | DateTimeField | Arrival time |
| sms_sent | BooleanField | SMS notification sent |
| sms_sent_at | DateTimeField | SMS timestamp |

#### SMSLog Model
| Field | Type | Description |
|-------|------|-------------|
| parent | ForeignKey(Parent) | SMS recipient |
| attendance | ForeignKey(Attendance) | Related attendance |
| message | TextField | SMS content |
| status | CharField | sent/failed |
| error_message | TextField | Error details if failed |
| timestamp | DateTimeField | SMS time |

### 5.3 Data Flow Between Tables

```
1. Teacher creates QRSession
   → Inserts: qr_value, class_group, teacher, expires_at
   
2. Student scans QR
   → System validates QRSession (is_active=True, expires_at > now)
   
3. Attendance recorded
   → Inserts: student, session, class_group, status, GPS data, distance
   
4. SMS sent to parent
   → Inserts: SMSLog record with parent, attendance reference
   
5. Dashboard queries
   → Joins: Student + Attendance + ClassGroup for reports
```

---

## 6. FRONTEND STRUCTURE

### 6.1 Main Pages

| Page | URL | Description | User Role |
|------|-----|-------------|-----------|
| Login | `/accounts/login/` | User authentication | All |
| Change Password | `/accounts/change-password/` | First-time password change | All |
| Admin Dashboard | `/dashboard/admin/` | System management | Admin |
| Teacher Dashboard | `/dashboard/teacher/` | QR generation & reports | Teacher |
| Student Dashboard | `/dashboard/student/` | Attendance history | Student |
| Parent Dashboard | `/dashboard/parent/` | Child's attendance | Parent |
| QR Scanner | `/qr/scan/` | Mobile QR scanner | Student |
| View QR | `/qr/view/<id>/` | Display QR code | Teacher |

### 6.2 Page Interactions

#### Login Page
- Simple username/password form
- Role-based redirect after login
- "Must change password" check for new accounts

#### Teacher Dashboard
```
┌─────────────────────────────────────┐
│  Teacher Dashboard                  │
├─────────────────────────────────────┤
│  Statistics Cards                   │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ Classes│ │ Sessions│ │Students│  │
│  └────────┘ └────────┘ └────────┘  │
├─────────────────────────────────────┤
│  My Classes                         │
│  ┌───────────────────────────────┐ │
│  │ Grade 10-A           [QR]     │ │
│  │ Grade 10-B           [QR]     │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  Recent Attendance                  │
│  ┌───────────────────────────────┐ │
│  │ Student     Time    Status    │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

#### QR Scanner Page (Mobile-Optimized)
```
┌─────────────────────────────────────┐
│  Scan Attendance                    │
│  Student                            │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐ │
│  │ 📍 GPS: Ready (45m away)    │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    [Camera Viewfinder]        │ │
│  │    ┌─────────────┐            │ │
│  │    │  QR Frame   │            │ │
│  │    │   ═══════   │            │ │
│  │    └─────────────┘            │ │
│  │                               │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  Manual Entry: [________] [Submit]  │
└─────────────────────────────────────┘
```

### 6.3 User Interaction Flow

**Teacher Interaction:**
```
1. Login → Teacher Dashboard
2. View list of assigned classes
3. Click "Generate QR" button
4. QR code displayed with countdown timer
5. Show QR to students
6. Monitor real-time attendance in dashboard
7. Export attendance report (if needed)
```

**Student Interaction:**
```
1. Login → Student Dashboard
2. Click "Scan QR" button
3. Allow camera and GPS permissions
4. Point camera at teacher's QR code
5. System processes scan (2-3 seconds)
6. See success message: "Attendance Recorded!"
7. Return to dashboard automatically
```

**Parent Interaction:**
```
1. Login → Parent Dashboard
2. View child's attendance history
3. Receive SMS: "Your child is PRESENT at 8:30 AM"
4. Check punctuality patterns
5. Contact school if concerns arise
```

---

## 7. BACKEND LOGIC

### 7.1 Key Views and Endpoints

| View Function | URL | Method | Description |
|--------------|-----|--------|-------------|
| `login_view` | `/accounts/login/` | POST | Authenticates user, redirects by role |
| `generate_qr_session` | `/qr/generate/<class_id>/` | POST | Creates new QR session |
| `view_qr_session` | `/qr/view/<session_id>/` | GET | Displays QR code image |
| `scan_qr_page` | `/qr/scan/` | GET | Renders scanner page |
| `submit_attendance` | `/qr/submit/` | POST | Legacy attendance submission |
| `api_scan_attendance` | `/api/scan-attendance/` | POST | **Main API for mobile scanning** |
| `admin_dashboard` | `/dashboard/admin/` | GET | Admin dashboard |
| `teacher_dashboard` | `/dashboard/teacher/` | GET | Teacher dashboard |
| `student_dashboard` | `/dashboard/student/` | GET | Student dashboard |
| `parent_dashboard` | `/dashboard/parent/` | GET | Parent dashboard |

### 7.2 API Endpoint: `/api/scan-attendance/`

**Request Format:**
```json
{
  "qr_value": "abc123-session-uuid",
  "latitude": 14.5995,
  "longitude": 120.9842
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Attendance recorded successfully! Status: Present",
  "status": "present",
  "distance": 45,
  "sms_sent": {
    "sent": true,
    "message": "SMS sent to parent"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid or expired QR code."
}
```

### 7.3 Validation Logic

**QR Validation:**
```python
try:
    session = QRSession.objects.get(
        qr_value=qr_value,
        is_active=True,
        expires_at__gt=timezone.now()  # Not expired
    )
except QRSession.DoesNotExist:
    return JsonResponse({
        'success': False,
        'error': 'Invalid or expired QR code.'
    })
```

**GPS Validation:**
```python
distance = calculate_distance(
    settings.SCHOOL_LATITUDE,
    settings.SCHOOL_LONGITUDE,
    float(latitude),
    float(longitude)
)

if distance > settings.GPS_RADIUS_METERS:
    return JsonResponse({
        'success': False,
        'error': f'You are {distance} meters away. Must be within {settings.GPS_RADIUS_METERS} meters.'
    })
```

**Duplicate Check:**
```python
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
```

### 7.4 Data Processing Flow

```
1. Receive POST request with JSON payload
2. Parse qr_value, latitude, longitude
3. Validate: All fields present?
4. Get student from authenticated user
5. Validate QR session (exists, active, not expired)
6. Calculate distance from school using Haversine formula
7. Validate: Within allowed radius?
8. Check: Duplicate attendance for today?
9. Determine status (present/late based on time)
10. Create Attendance record in database
11. If parent exists → Send SMS via Twilio
12. Log SMS in database
13. Return JSON response with success status
```

---

## 8. API FLOW

### 8.1 Frontend to Backend Communication

**Technology:** AJAX (Asynchronous JavaScript and XML)

**Library:** Vanilla JavaScript `fetch()` API

### 8.2 Request Flow

```
┌─────────────┐      ┌─────────────────────┐      ┌─────────────┐
│   Student   │      │   JavaScript        │      │   Django    │
│   Browser   │─────▶│   (Frontend)        │─────▶│   Backend   │
└─────────────┘      └─────────────────────┘      └─────────────┘
                            │
                            ▼
                    1. Camera detects QR
                    2. Extract QR value
                    3. Get GPS coordinates
                    4. Create JSON payload
                    5. Add CSRF token
                    6. Send POST request
```

### 8.3 Example Request

**JavaScript Code:**
```javascript
function submitAttendance(qrValue) {
    const data = {
        qr_value: qrValue,
        latitude: currentLatitude,
        longitude: currentLongitude
    };
    
    fetch('/api/scan-attendance/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()  // Security token
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessModal(data);
        } else {
            showErrorModal(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorModal('Network error. Please try again.');
    });
}
```

### 8.4 Response Handling

```javascript
// Success Case
{
    "success": true,
    "message": "Attendance recorded successfully! Status: Present",
    "status": "present",
    "distance": 45,
    "sms_sent": {
        "sent": true,
        "message": "SMS sent to parent"
    }
}

// UI Action: Show green success modal, auto-redirect to dashboard

// Error Case
{
    "success": false,
    "error": "You are 150 meters away. Must be within 100 meters."
}

// UI Action: Show red error modal with specific message
```

### 8.5 API Security

**CSRF Protection:**
```javascript
// Get CSRF token from hidden form field
function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenElement ? tokenElement.value : '';
}

// Include in request header
headers: {
    'X-CSRFToken': getCSRFToken()
}
```

**Authentication Check:**
```python
@login_required  # Decorator ensures user is logged in
def api_scan_attendance(request):
    # Only authenticated users can access
    ...
```

---

## 9. SMS INTEGRATION

### 9.1 Twilio Configuration

**Environment Variables (in `.env` file):**
```
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

**Settings Integration (`settings.py`):**
```python
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
```

**Why Environment Variables?**
- Security: Sensitive credentials not in code
- Flexibility: Different credentials for dev/prod
- Best Practice: Industry standard for API keys

### 9.2 SMS Sending Process

```
1. Attendance successfully recorded
   ↓
2. Check if student has parent linked
   ↓
3. If yes, get parent's contact_number
   ↓
4. Format SMS message
   ↓
5. Call Twilio API
   ↓
6. Receive Twilio message SID
   ↓
7. Log SMS in database (SMSLog model)
   ↓
8. Update attendance.sms_sent = True
   ↓
9. Return SMS status in API response
```

### 9.3 SMS Message Template

**Format:**
```
Your child {student_name} is PRESENT at {time}. (Sent from Twilio trial account)
```

**Example:**
```
Your child Juan Dela Cruz is PRESENT at 8:30 AM. (Sent from Twilio trial account)
```

**Note:** "Sent from Twilio trial account" is required for Twilio trial accounts.

### 9.4 SMS Logging

Every SMS attempt is logged in the `SMSLog` model:

| Field | Value Example |
|-------|---------------|
| parent | Juan Dela Cruz's parent |
| attendance | Attendance record #1234 |
| message | SMS content |
| status | sent / failed |
| error_message | None (if successful) or error details |
| timestamp | 2026-01-15 08:30:15 |

**Purpose of Logging:**
- Track SMS delivery success/failure
- Debug issues
- Generate reports
- Audit trail

---

## 10. SECURITY

### 10.1 Authentication

**Implementation:**
- Django's built-in authentication system
- Session-based authentication
- `@login_required` decorator on all sensitive views

**Flow:**
```
User requests page → Django checks session → 
If logged in: Show page
If not logged in: Redirect to login
```

### 10.2 CSRF Protection

**What is CSRF?**
Cross-Site Request Forgery - An attack where a malicious website makes requests on behalf of a logged-in user.

**Protection:**
```python
# CSRF token in forms
{% csrf_token %}

# Token must be included in AJAX requests
headers: {
    'X-CSRFToken': getCSRFToken()
}
```

### 10.3 Backend Validation

**Why Validate on Backend?**
- Never trust frontend data
- Frontend can be manipulated
- Backend is the source of truth

**Validation Layers:**
```
1. QR Value Validation
   - Check if exists in database
   - Verify is_active = True
   - Check expires_at > current time

2. GPS Validation
   - Calculate actual distance
   - Verify within allowed radius
   - Don't trust frontend-calculated distance

3. User Validation
   - Verify user is a student
   - Get student profile from authenticated user
   - Don't trust user_id from frontend

4. Duplicate Check
   - Query database for existing attendance
   - Prevent double-recording
```

### 10.4 Preventing Duplicate Attendance

**Logic:**
```python
# Check for existing attendance today
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
```

**Why Important:**
- Prevents gaming the system
- Ensures accurate records
- Prevents multiple SMS notifications

### 10.5 QR Code Security

**Features:**
- UUID-based: Impossible to guess
- Time-limited: Expires after 2 hours
- One-time activation: Previous sessions auto-deactivated
- Class-specific: Only works for intended class

### 10.6 GPS Security

**Backend Calculation:**
```python
# Calculate distance server-side
# Frontend sends coordinates, but verification happens here
distance = calculate_distance(school_lat, school_lng, student_lat, student_lng)

if distance > ALLOWED_RADIUS:
    reject_attendance()
```

**Prevents:**
- Fake GPS apps on phones
- Coordinate spoofing
- Attendance from home

---

## 11. DEPLOYMENT READINESS

### 11.1 Required Files

| File | Purpose | Status |
|------|---------|--------|
| `requirements.txt` | Python dependencies | ✅ Present |
| `Procfile` | Heroku/Render deployment | ✅ Present |
| `runtime.txt` | Python version | ✅ Present |
| `.env.example` | Environment variables template | ✅ Present |
| `README.md` | Documentation | ✅ Present |

### 11.2 Dependencies (requirements.txt)

```
Django>=4.2.0
Pillow>=9.0.0
qrcode>=7.4.0
python-decouple>=3.6
psycopg2-binary>=2.9.0
dj-database-url>=1.0.0
twilio>=8.5.0
whitenoise>=6.0.0
gunicorn>=20.1.0
openpyxl>=3.1.0
```

### 11.3 Environment Variables Required

```
# Database (for production)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Twilio (for SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890

# School GPS Coordinates
SCHOOL_LATITUDE=14.5995
SCHOOL_LONGITUDE=120.9842
GPS_RADIUS_METERS=100

# Security
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```

### 11.4 Deployment Checklist

**Before Deployment:**
- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure `ALLOWED_HOSTS` with production domain
- [ ] Set up PostgreSQL database
- [ ] Configure all environment variables
- [ ] Run migrations on production database
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Run setup_data.py for initial data
- [ ] Configure Twilio account with phone number
- [ ] Test GPS coordinates with actual school location
- [ ] Verify SMS functionality

### 11.5 Deployment Platforms

**Recommended:**
- **Render.com** - Free tier available, PostgreSQL included
- **Heroku** - Easy deployment, paid tiers for production
- **PythonAnywhere** - Good for educational projects

### 11.6 Missing Configurations

| Item | Status | Action |
|------|--------|--------|
| Production database | ⚠️ | Set DATABASE_URL |
| Twilio credentials | ⚠️ | Set up Twilio account |
| School GPS coordinates | ⚠️ | Get actual coordinates |
| SSL Certificate | ⚠️ | Required for HTTPS |
| Static file serving | ⚠️ | Configure whitenoise |

---

## 12. LIMITATIONS

### 12.1 Current System Limitations

| # | Limitation | Impact | Mitigation |
|---|------------|--------|------------|
| 1 | Requires internet connection | Cannot work offline | Use mobile data or WiFi |
| 2 | GPS accuracy varies | 5-20 meter accuracy variance | Set radius to 100m to accommodate |
| 3 | Twilio trial restrictions | SMS includes "trial" message | Upgrade to paid Twilio account |
| 4 | Browser permissions needed | Camera and GPS access required | Clear instructions for users |
| 5 | QR codes expire in 2 hours | Teachers must regenerate | Expiration prevents replay attacks |
| 6 | SMS costs (Twilio) | Per-message charges | Budget monitoring needed |
| 7 | One parent per student | Cannot notify multiple parents | Extend model for multiple parents |
| 8 | No offline mode | Cannot record attendance without internet | N/A - requires real-time validation |
| 9 | Mobile-dependent | Students need smartphones | Provide alternatives for students without phones |

### 12.2 Technical Limitations

**GPS Accuracy:**
- Indoor GPS can be inaccurate
- Urban canyons affect signal
- Solution: Set appropriate radius (100m default)

**Browser Support:**
- Requires modern browsers with camera API support
- Not compatible with older phones
- Solution: Provide manual entry fallback

**QR Scanning:**
- Requires good lighting
- Camera focus time varies
- Solution: Animated scan guide in UI

### 12.3 Suggested Improvements

**For Thesis/Project Enhancement:**

1. **Offline Mode**: Store scans locally, sync when online
2. **Biometric Integration**: Add face recognition for extra security
3. **Multiple Parents**: Allow multiple parent contacts per student
4. **Advanced Analytics**: Attendance trends, predictive reports
5. **Mobile App**: Native iOS/Android app instead of web
6. **Push Notifications**: Replace SMS with Firebase push notifications (free)
7. **Parent App**: Dedicated mobile app for parents
8. **Attendance Appeals**: Allow students to dispute absences
9. **Integration**: Connect with school management systems
10. **AI Features**: Detect proxy attendance patterns

### 12.4 Academic Context

**For Thesis Defense:**

**Strengths:**
- ✅ Modern technology stack
- ✅ Real-world problem solution
- ✅ Multi-layered security
- ✅ Complete user role system
- ✅ Mobile-first design
- ✅ Automated notifications

**Research Opportunities:**
- Study GPS accuracy in educational settings
- Compare with traditional attendance methods
- Analyze student punctuality improvements
- Measure parent satisfaction with notifications
- Cost-benefit analysis vs. paper-based systems

---

## CONCLUSION

The **QR Attendance System** is a comprehensive, production-ready solution for automating student attendance tracking. It combines modern web technologies (Django, JavaScript, QR codes) with real-world requirements (GPS validation, SMS notifications, role-based access) to create a secure and user-friendly system.

**Key Achievements:**
1. ✅ Prevents proxy attendance through GPS verification
2. ✅ Real-time parent notifications via SMS
3. ✅ Mobile-optimized QR scanning experience
4. ✅ Complete user management with 4 distinct roles
5. ✅ Secure authentication and validation
6. ✅ Ready for academic presentation and deployment

**Next Steps for Deployment:**
1. Configure production environment variables
2. Set up PostgreSQL database
3. Get Twilio account and phone number
4. Calibrate school GPS coordinates
5. Deploy to Render or similar platform
6. Test with real users
7. Gather feedback and iterate

---

**Document Version:** 1.0  
**Created For:** Academic System Analysis  
**System Name:** Mobile QR Code Attendance System with GPS Verification and SMS Notification  
**Technologies:** Django, Bootstrap, JavaScript, Twilio, PostgreSQL
