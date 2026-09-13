# Class Sync

Class Sync is a comprehensive, Django-based application designed to manage university/school classes, OTP-based attendance, faculty absences and substitutions, student assignments, and notifications seamlessly.

## 🌟 Features

### 1. Core Management
- **Role-Based Access**: Specialized views for Administrators, Faculty, and Students.
- **Academic Structure**: Manage Departments, Courses, and Sections efficiently.
- **Timetable Scheduling**: Create and manage weekly timetable slots for various sections and faculties.

### 2. Attendance Management
- **OTP-Based Attendance**: Secure session-based attendance using OTPs.
- **Threshold Alerts**: Automated warnings for students falling below the minimum required attendance.

### 3. Absence & Substitutions
- **Absence Reporting**: Faculty can log upcoming absences for specific timetable slots.
- **Substitution Requests**: The system handles substitution matching based on faculty availability and schedules.

### 4. Assignments
- **Creation & Management**: Faculty can create assignments with descriptions and due dates.
- **Submissions**: Students can submit their work directly through the platform.
- **Automated Reminders**: Keep track of pending assignments.

### 5. Notifications
- **System Announcements**: Global announcements for all users.
- **Early Warnings & Risk Flags**: Identify and notify students at risk based on their performance and attendance.

---

## 🚀 Getting Started

Follow these steps to run the application locally on your machine in a few minutes.

### Prerequisites
- **Python 3.10+**
- **pip** (Python package installer)

### 1. Clone & Setup Virtual Environment
It's recommended to use a virtual environment to keep dependencies isolated.
```bash
# Navigate to the project directory
cd classsync

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (where `manage.py` is). You can copy the provided example file:
```bash
cp .env.example .env
```
*(Ensure you have a generated `SECRET_KEY` and `DEBUG=True` for local development).*

### 4. Setup Database
Run the migrations to create the database tables (SQLite by default).
```bash
python manage.py migrate
```

### 5. Seed the Database (Demo Data)
To easily test out the application, you can seed the database with mock data. This creates students, faculties, courses, and sample assignments automatically.
```bash
python manage.py seed_demo
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
The application will now be running at `http://127.0.0.1:8000/`.

---

## 🧪 About the Seeded Database

If you ran the `python manage.py seed_demo` command, your database is now populated with the following data:

- **1 Department**: Computer Science & Engineering (CS)
- **3 Courses & 3 Sections**
- **Timetable Slots** from Monday to Friday
- **3 Sample Assignments**
- **1 Sample Absence Report**

### 🔑 Demo Login Credentials
Use the following credentials to explore different roles (Password for all generated users is based on their role):

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin_demo` | `Admin@1234` |
| **Faculty** | `alice.sharma` | `Faculty@1234` |
| **Student** | `s001` | `Student@1234` |

*(Note: The seed script creates 5 faculties and 15 students in total. Other student usernames range from `s001` to `s015`.)*

---

## 🛠️ Management Commands

Class Sync includes several background tasks and commands that can be run manually or configured via cron/APScheduler:

- **Seed Demo Data**: `python manage.py seed_demo`
- **Check Confirmation Timeouts (Absence)**: `python manage.py check_confirmation_timeouts`
- **Send Assignment Reminders**: `python manage.py send_assignment_reminders`
- **Evaluate Early Warnings (Notifications)**: `python manage.py evaluate_early_warning`

---

## Android app

The native Compose client lives in `classsync-android/`. Debug builds target
`http://10.0.2.2:8000/`, the Android emulator alias for the development
machine. For a physical device, change the debug `BASE_URL` to a reachable
HTTPS endpoint (or tunnel) and add its host to `ALLOWED_HOSTS`.

Open `classsync-android/` in Android Studio using JDK 17, then build the debug
variant. The client supports Android 8.0+ (API 26). Verify the server API with:

```bash
python manage.py test api
```

### Firebase push setup

1. Put the Firebase Android `google-services.json` in `classsync-android/app/`.
   The Gradle Google Services plugin activates automatically when the file is present.
2. Install `firebase-admin` from `requirements.txt`, then set
   `FIREBASE_CREDENTIALS` to the deployed server's service-account JSON path.
3. Rebuild the app and sign in once to register its FCM device token.

Before Firebase is configured, notifications are still saved and displayed
in-app; server push delivery is safely skipped.

### Test and release build

Use JDK 17 and an Android SDK containing platform 35, then run:

```powershell
cd classsync-android
.\gradlew.bat test lint assembleDebug
```

For a signed release, copy the values from
`classsync-android/gradle.properties.example` into an untracked Gradle
properties file (or provide them as `-P` arguments), then run:

```powershell
.\gradlew.bat bundleRelease
```

The release AAB is written to `app/build/outputs/bundle/release/`. Signing
material, Firebase configuration, and generated Android build files are
excluded from version control.
