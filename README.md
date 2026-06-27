# 🏥 Hospital Management System (HMS)

A production-quality Mini Hospital Management System built with Django 5, Django REST Framework, MySQL, Serverless email delivery, and Google Calendar integration.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Setup and Run](#setup-and-run)
- [API Endpoints](#api-endpoints)
- [The Design Decision](#the-design-decision)
- [Limitations](#limitations)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client (REST API Consumer)                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Django 5 + DRF Application                        │
│                                                                      │
│  ┌───────────┐  ┌──────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ accounts  │  │   doctors    │  │  patients  │  │availability │  │
│  │ (auth)    │  │  (profile,   │  │ (profile,  │  │  (slots,    │  │
│  │           │  │  dashboard,  │  │  bookings, │  │  CRUD,      │  │
│  │ Signup    │  │  bookings)   │  │  dr.list)  │  │  overlap)   │  │
│  │ Login     │  │              │  │            │  │             │  │
│  │ Logout    │  └──────────────┘  └────────────┘  └─────────────┘  │
│  └───────────┘                                                       │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐   │
│  │    appointments      │    │         calendar_service         │   │
│  │                      │    │                                  │   │
│  │  select_for_update() │    │  Google OAuth2 flow              │   │
│  │  transaction.atomic()│    │  Create events (doctor+patient)  │   │
│  │  Booking logic       │    │  Store tokens in DB              │   │
│  └──────────────────────┘    └──────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    email_client                              │   │
│  │            HTTP POST → Serverless Email Service              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
        ┌────────────┐  ┌─────────────┐  ┌────────────────────┐
        │   MySQL    │  │Google       │  │ Serverless Email    │
        │  Database  │  │Calendar API │  │ Service             │
        │            │  │(OAuth2)     │  │ (serverless-offline │
        │  6 tables  │  │             │  │  port 3001)         │
        └────────────┘  └─────────────┘  └────────────────────┘
```

### App Responsibilities

| App | Responsibility |
|-----|---------------|
| `accounts` | Custom User model (email + role), signup, login, logout, session auth |
| `doctors` | Doctor profile, dashboard, view own bookings |
| `patients` | Patient profile, dashboard, browse doctors, booking history |
| `availability` | Doctor creates/edits/deletes time slots; patient browses future slots |
| `appointments` | Atomic booking with race-condition protection |
| `calendar_service` | Google OAuth2 flow, create calendar events post-booking |
| `email_client` | HTTP client that calls the external email microservice |
| `email-service` | Standalone serverless Python function — Gmail SMTP email delivery |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 5.0 |
| REST API | Django REST Framework 3.15 |
| Database | MySQL 8+ |
| ORM | Django ORM |
| Authentication | Session Authentication |
| Email | Serverless Framework + serverless-offline + Gmail SMTP |
| Calendar | Google Calendar API v3 + OAuth2 |
| Python | 3.12 |

---

## Setup and Run

### Prerequisites

- Python 3.12
- MySQL 8+
- Node.js 18+ and npm (for serverless-offline)
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords)
- (Optional) Google Cloud project with Calendar API enabled

---

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Hospital-HMS.git
cd Hospital-HMS
```

### 2. Create MySQL database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE hms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 3. Set up Django backend

```bash
cd hms

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate.bat     # Windows

# Install dependencies
pip install -r ../requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DB_PASSWORD, and optionally Google credentials
nano .env
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional, for admin panel)

```bash
python manage.py createsuperuser
```

### 6. Start Django development server

```bash
python manage.py runserver
# API available at http://localhost:8000
```

---

### 7. Set up and start the Email Service

In a **new terminal**:

```bash
cd email-service

# Install serverless and serverless-offline
npm install

# Configure Gmail credentials
cp .env.example .env
nano .env   # Set GMAIL_USER and GMAIL_APP_PASSWORD

# Start serverless-offline
npx serverless offline
# Email service runs at http://localhost:3001
```

**Health check:**
```bash
curl http://localhost:3001/dev/email/health
```

---

### 8. Google Calendar Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Calendar API**
3. Create **OAuth 2.0 Client ID** (Web application)
4. Add `http://localhost:8000/api/calendar/oauth2/callback/` as an authorised redirect URI
5. Copy Client ID and Secret into `hms/.env`

To connect a user's calendar:
```bash
# Step 1 — get the authorization URL (user must be logged in)
GET /api/calendar/authorize/

# Step 2 — open the returned URL in a browser, grant access
# Google redirects to /api/calendar/oauth2/callback/ automatically

# Step 3 — check connection status
GET /api/calendar/status/
```

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup/` | None | Register as Doctor or Patient |
| POST | `/api/auth/login/` | None | Login (creates session) |
| POST | `/api/auth/logout/` | Any | Logout (destroys session) |
| GET | `/api/auth/me/` | Any | Get current user info |

**Signup body example:**
```json
{
  "email": "doctor@example.com",
  "password": "securepass123",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "doctor"
}
```

---

### Doctor APIs (`/api/doctors/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/doctors/dashboard/` | Doctor | Dashboard + upcoming bookings |
| GET | `/api/doctors/profile/` | Doctor | View own profile |
| PUT/PATCH | `/api/doctors/profile/` | Doctor | Update own profile |
| GET | `/api/doctors/bookings/` | Doctor | View own patient bookings |

---

### Patient APIs (`/api/patients/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/patients/dashboard/` | Patient | Dashboard summary |
| GET | `/api/patients/profile/` | Patient | View own profile |
| PUT/PATCH | `/api/patients/profile/` | Patient | Update own profile |
| GET | `/api/patients/doctors/` | Patient | Browse all active doctors |
| GET | `/api/patients/bookings/` | Patient | View own booking history |

---

### Availability APIs (`/api/availability/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/availability/` | Doctor | List own availability slots |
| POST | `/api/availability/` | Doctor | Create new slot |
| GET | `/api/availability/<id>/` | Doctor | Retrieve a slot |
| PUT/PATCH | `/api/availability/<id>/` | Doctor | Update a slot |
| DELETE | `/api/availability/<id>/` | Doctor | Delete a slot |
| GET | `/api/availability/doctor/<doctor_id>/` | Patient | Browse a doctor's future open slots |

**Create slot body example:**
```json
{
  "start_time": "2025-06-15T09:00:00Z",
  "end_time": "2025-06-15T09:30:00Z",
  "notes": "Morning consultation"
}
```

---

### Appointment APIs (`/api/appointments/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/appointments/book/` | Patient | Book an available slot |
| GET | `/api/appointments/<id>/` | Doctor/Patient | Get appointment detail |

**Book appointment body:**
```json
{
  "availability_id": 42,
  "notes": "Follow-up consultation"
}
```

---

### Calendar APIs (`/api/calendar/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/calendar/authorize/` | Any | Get Google OAuth2 URL |
| GET | `/api/calendar/oauth2/callback/` | Any | OAuth2 callback (Google redirects here) |
| GET | `/api/calendar/status/` | Any | Check if calendar is connected |
| DELETE | `/api/calendar/disconnect/` | Any | Disconnect Google Calendar |

---

### Email Service (`http://localhost:3001/dev/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dev/email/send` | Send an email (SIGNUP_WELCOME or BOOKING_CONFIRMATION) |
| GET | `/dev/email/health` | Health check |

---

## The Design Decision

### Race Condition Handling in Appointment Booking

This is the most critical piece of the system. When multiple patients try to book the same slot simultaneously, a naive implementation leads to **double booking**.

---

#### Option 1 — Simple Query (Incorrect)

```python
# DANGEROUS — race condition exists here
slot = DoctorAvailability.objects.get(pk=availability_id)

if slot.is_booked:  # READ
    raise ValidationError("Slot already booked.")

slot.is_booked = True  # CHECK-THEN-ACT gap
slot.save()
Appointment.objects.create(patient=patient, availability=slot)
```

**The Problem:**

```
Time →   Request A              Request B
T1       GET slot → is_booked=False
T2                              GET slot → is_booked=False
T3       CHECK: False → proceed
T4                              CHECK: False → proceed
T5       SET is_booked=True
T6       CREATE Appointment ✓
T7                              SET is_booked=True
T8                              CREATE Appointment ✓  ← DOUBLE BOOKING!
```

Both requests read `is_booked=False` before either writes `True`. This is a **Time-Of-Check/Time-Of-Use (TOCTOU)** race condition. The result is two Appointment rows for the same slot.

---

#### Option 2 — `transaction.atomic()` + `select_for_update()` (Implemented ✓)

```python
@transaction.atomic
def book_slot(patient, availability_id, notes=""):
    # Acquire row-level EXCLUSIVE lock on the slot row
    slot = (
        DoctorAvailability.objects
        .select_for_update()   # ← SELECT ... FOR UPDATE
        .get(pk=availability_id)
    )

    # Re-check inside the lock (safe)
    if slot.is_booked:
        raise ValidationError("Slot already booked.")

    slot.is_booked = True
    slot.save()
    return Appointment.objects.create(patient=patient, availability=slot)
```

**How it works:**

```
Time →   Request A                    Request B
T1       BEGIN TRANSACTION
T2       SELECT ... FOR UPDATE        (blocked — waits for lock)
T3       CHECK: is_booked=False
T4       SET is_booked=True, SAVE
T5       CREATE Appointment ✓
T6       COMMIT (releases lock)
T7                                    (unblocked, reads row)
T8                                    CHECK: is_booked=True
T9                                    RAISE ValidationError 409 ✓
```

**Why Option 2 is correct:**

- `SELECT FOR UPDATE` issues a `SELECT ... FOR UPDATE` SQL statement. MySQL acquires a **row-level exclusive lock**.
- Any other transaction trying to lock the same row **blocks** (waits) until the first transaction commits.
- Once the lock releases, the second transaction re-reads the row and correctly sees `is_booked=True`.
- No application-level mutexes, no Redis, no queues — the database does the work.
- The lock is automatically released when `transaction.atomic()` commits or rolls back.

**Why not use `UPDATE ... WHERE is_booked=False`?**

An optimistic `UPDATE` approach is also valid, but requires checking `rows_affected`. `select_for_update()` is more readable, integrates naturally with Django ORM, and gives us the slot object to work with before committing — making additional checks (e.g., same-day duplicate prevention) straightforward within the same transaction.

---

## Limitations

1. **No token refresh UI flow** — Google OAuth2 tokens are refreshed automatically server-side, but if the refresh token is revoked, the user must re-authorise via `/api/calendar/authorize/`.

2. **Email delivery is best-effort** — Email failures are logged but do not affect booking. If the serverless service is down, emails are silently dropped. A production system should use a message queue (SQS, Celery + Redis) with retry logic.

3. **No appointment cancellation endpoint** — The Appointment model has a `status` field supporting `cancelled`, but no view exposes this yet. This is a straightforward addition.

4. **No pagination** — List endpoints return all records. Production deployments should add `PageNumberPagination` in DRF settings.

5. **Session-based auth is not stateless** — Django sessions are stored in the database (`django_session` table). High-traffic deployments should consider Redis session backend.

6. **Google Calendar is optional** — If a user hasn't connected their Google Calendar, events are skipped silently. This is by design (graceful degradation), but users are not notified in-app.

7. **Single-timezone system** — All datetimes are stored and returned in UTC. A multi-timezone UI layer would need to handle conversion on the client side.

8. **No file uploads** — Doctor/Patient profiles don't support profile photos. Adding this would require configuring Django's media file handling and a storage backend (e.g., S3).

---

## Project Structure

```
Hospital-HMS/
├── README.md
├── requirements.txt
├── sample_db_setup.sql
├── ai-tool-usage-log/
│   └── chatgpt-thread.md
├── hms/
│   ├── manage.py
│   ├── .env.example
│   ├── .env                        ← create from .env.example
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── exceptions.py
│   ├── accounts/                   ← User model, auth views
│   ├── doctors/                    ← Doctor profile + dashboard
│   ├── patients/                   ← Patient profile + dashboard
│   ├── availability/               ← Slot CRUD + overlap detection
│   ├── appointments/               ← Atomic booking service
│   ├── calendar_service/           ← Google Calendar OAuth2 + events
│   └── email_client/               ← HTTP client → email service
└── email-service/
    ├── serverless.yml
    ├── handler.py                  ← Gmail SMTP email delivery
    ├── requirements.txt
    ├── package.json
    └── .env.example
```

---

## Video Demo Checklist

- [ ] Doctor signup → receives welcome email
- [ ] Patient signup → receives welcome email
- [ ] Doctor logs in → views dashboard
- [ ] Doctor creates availability slots
- [ ] Doctor edits an availability slot
- [ ] Doctor deletes an availability slot
- [ ] Patient logs in → views doctor list
- [ ] Patient browses a doctor's available slots
- [ ] Patient books a slot → receives confirmation email
- [ ] Booked slot no longer appears as available
- [ ] Doctor views their bookings (only own)
- [ ] Patient views booking history
- [ ] Second patient attempts to book same slot → 409 Conflict
- [ ] Google Calendar event appears in doctor's calendar (if connected)
- [ ] Google Calendar event appears in patient's calendar (if connected)
- [ ] Doctor cannot access patient APIs (403)
- [ ] Patient cannot access doctor APIs (403)
- [ ] Serverless email service health check: `GET /dev/email/health`
