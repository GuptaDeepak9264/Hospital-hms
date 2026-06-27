# AI Tool Usage Log — HMS Project

## Tool Used
**Claude (Anthropic)** — used as an AI coding assistant throughout this project.

---

## Conversation Thread

### Prompt 1
**User:**
> You are a Senior Python Backend Engineer. I have a backend assessment PDF for a Mini Hospital Management System (HMS). Build the ENTIRE project exactly according to the requirements. [full spec provided]

**AI Response Summary:**
Understood the full specification. Began generating the project scaffold:
- Created `Hospital-HMS/` directory structure
- Wrote `requirements.txt` for Django 5 + DRF + MySQL + Google APIs
- Generated `hms/manage.py` and `config/settings.py` (MySQL, sessions, DRF, logging)
- Wrote `config/urls.py` routing all six app namespaces
- Created `config/exceptions.py` with a global JSON exception handler

---

### Prompt 2
**User:**
> Continue

**AI Response Summary:**
Continued file generation:
- `accounts/` app: custom `User` model (email-based, role field), `UserManager`, `SignupSerializer`, `LoginSerializer`, `UserSerializer`, `IsDoctorUser`/`IsPatientUser` permission classes, `AuthService` (signup + welcome email hook), `SignupView`, `LoginView`, `LogoutView`, `MeView`
- `doctors/` app: `Doctor` profile model, auto-create signal, `DoctorProfileSerializer`, `DoctorListSerializer`, `DoctorDashboardView`, `DoctorProfileView`, `DoctorBookingsView`
- `patients/` app: `Patient` profile model, auto-create signal, patient views (dashboard, profile, doctor list, booking history)
- `availability/` app: `DoctorAvailability` model, overlap-detection in `AvailabilityService`, CRUD views for doctor + patient browse endpoint
- `appointments/` app: `Appointment` model with `select_for_update()` locking in `AppointmentService.book_slot()`
- `calendar_service/` app: `GoogleOAuth2Credential` model, OAuth2 flow with `google-auth-oauthlib`, `CalendarService.create_booking_events()`
- `email_client/client.py`: HTTP client calling the serverless email service
- `email-service/handler.py`: standalone Python serverless handler — `send_email` + `health_check` Lambda functions, Gmail SMTP via `smtplib`, HTML email templates for `SIGNUP_WELCOME` and `BOOKING_CONFIRMATION`
- All Django migrations (hand-written to match models exactly)
- `.env.example`, `serverless.yml`, `package.json`

---

### Key Design Decisions Discussed

**Q: How to handle race conditions in booking?**

AI explained two approaches:
1. **Option 1 (naive):** Read → check → write. Vulnerable to TOCTOU race condition.
2. **Option 2 (chosen):** `transaction.atomic()` + `select_for_update()` — acquires a DB row lock, guarantees mutual exclusion at the database level.

AI defended Option 2: it eliminates double-booking without application-level locking, queues, or Redis.

**Q: Why session auth over JWT?**

Per the spec. Session auth is simpler for same-origin clients and avoids token refresh complexity.

**Q: Why a separate email service?**

The spec requires a serverless microservice (Serverless Framework + serverless-offline) that Django calls over HTTP. This decouples email infrastructure from the core app — the email service can be deployed to AWS Lambda independently.

---

## AI Assistance Summary

| Area | AI Contribution |
|------|----------------|
| Architecture | Full Django app layout, clean separation of models/serializers/services/views |
| Models | Custom AbstractBaseUser, profile models, signals |
| Race conditions | Explained and implemented `select_for_update()` pattern |
| Google OAuth2 | Full token exchange and credential storage |
| Serverless | `serverless.yml`, handler with HTML email templates |
| Migrations | Hand-crafted migrations matching every model field |
| README | Professional documentation with architecture diagram |

---

*All code was reviewed and is production-quality. No TODOs remain.*
