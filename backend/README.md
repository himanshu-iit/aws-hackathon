# Event Tracker — Flask Backend

Python Flask backend for the Event Entry Guest Tracker. Phase 2 (Backend
Foundation) is complete: project structure, config, ORM models, core services,
logging, middleware, and the API blueprint skeleton.

## Structure

```
backend/
├── wsgi.py                  # Gunicorn / dev-server entrypoint (wsgi:app)
├── config.py                # Config classes (dev / staging / prod / testing)
├── requirements.txt
├── Dockerfile               # python:3.11-slim + gunicorn, non-root user
├── .dockerignore
├── .env.example
├── pytest.ini
├── app/
│   ├── factory.py           # create_app() application factory
│   ├── extensions.py        # db (SQLAlchemy), ma (Marshmallow)
│   ├── logging_config.py    # structured JSON logging -> stdout/CloudWatch
│   ├── middleware.py        # request id, access log, security headers, errors
│   ├── models/              # SQLAlchemy ORM
│   │   ├── base.py          # BaseModel: uuid id, timestamps, soft-delete
│   │   ├── user.py          # User / MasterUser / Volunteer (STI)
│   │   ├── auth.py          # OTPRequest, SessionToken, AuditLog
│   │   ├── guest.py         # Guest, Event, EventSession, Location
│   │   └── attendance.py    # CheckInEvent, CheckOutEvent, SessionAttendance
│   ├── services/            # business logic
│   │   ├── phone_validator.py
│   │   ├── otp_service.py
│   │   ├── session_service.py
│   │   └── notification_service.py  # Email (SendGrid) + SMS (Twilio)
│   └── blueprints/          # API routes (health live; others stubbed per phase)
└── tests/                   # pytest + hypothesis property tests
```

## Local development

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env       # optional; defaults to local SQLite
python wsgi.py               # http://localhost:5000/api/health
```

With no `DATABASE_URL`, the app uses a local SQLite file and auto-creates
tables, so it runs without a MySQL server. In AWS it connects to RDS MySQL via
the `DATABASE_URL` injected from Secrets Manager.

## Tests

```bash
cd backend
python -m pytest
```

Includes property-based tests (Hypothesis):
- **Property 2** — phone normalization idempotence
- **Property 13** — data persistence round-trip

## Phase status

| Area | Status |
|------|--------|
| Project setup, config, Docker | ✅ Phase 2 |
| ORM models (all entities) | ✅ Phase 2 |
| Phone / OTP / Session / Notification services | ✅ Phase 2 |
| CloudWatch JSON logging | ✅ Phase 2 |
| CORS, security headers, error handling | ✅ Phase 2 |
| Blueprint skeleton + `/api/health` | ✅ Phase 2 |
| Auth endpoints | ⏳ Phase 4 |
| Guest management | ⏳ Phase 5 |
| Check-in / check-out | ⏳ Phase 6 |
| Dashboard / analytics / export | ⏳ Phase 7–8 |
| Natural language queries | ⏳ Phase 9 |

Not deployed — build only.
