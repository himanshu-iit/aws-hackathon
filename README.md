# Event Entry Guest Tracker

![Backend](https://img.shields.io/badge/Backend-Flask%20%2F%20Python-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2F%20TypeScript-61dafb)
![Infra](https://img.shields.io/badge/Infra-AWS%20CloudFormation-orange)
![Database](https://img.shields.io/badge/DB-MySQL%20RDS-green)

A cloud-native event guest-tracking system for managing guest registration,
volunteer-assisted check-in/check-out, and real-time attendance analytics —
with **per-event scoping** so each event's data stays isolated.

> **Live demo:** https://d2y60we8f8rlpl.cloudfront.net

---

## What it does

- **Master users** create an event (identified by a 2-digit ID) and administer it.
- **Volunteers** self-register into an existing event and assist with guest operations.
- **Guests** are registered and checked in/out by masters or volunteers (no self-service).
- **Real-time dashboard** and **analytics** show attendance, categories, capacity, and hourly trends.
- **Event isolation** — users only see the data for the event they logged into.

---

## Architecture

```
Browser (HTTPS)
   │
   ▼
CloudFront ──► S3            (React SPA — static assets)
   │
   └── /api/* ──► ALB ──► ECS Fargate (Flask) ──► RDS MySQL
                                │
                                └──► CloudWatch Logs
```

- The browser only ever talks **HTTPS to CloudFront**. CloudFront serves the
  React app from S3 and **proxies `/api/*` to the ALB** (same-origin, so no CORS
  and no mixed-content issues).
- The Flask backend runs as containers on **ECS Fargate** behind an **ALB**.
- Data is stored in **MySQL on RDS**; logs stream to **CloudWatch**.
- All infrastructure is defined as **CloudFormation** templates.

### Technology stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, React Router, Context API, Axios |
| Backend | Python 3.11, Flask, Flask-SQLAlchemy, Gunicorn |
| Database | MySQL 8.0 (Amazon RDS, single-AZ) |
| Hosting | S3 + CloudFront (frontend), ECS Fargate + ALB (backend) |
| Registry | Amazon ECR |
| Secrets | AWS Secrets Manager |
| Logging | AWS CloudWatch Logs |
| IaC | AWS CloudFormation |

---

## Repository layout

```
zerotohero/
├── backend/                     # Flask API
│   ├── app/
│   │   ├── factory.py           # app factory
│   │   ├── models/              # SQLAlchemy models (user, guest, auth, attendance)
│   │   ├── services/            # phone/OTP/session/analytics/checkin/limits
│   │   ├── blueprints/          # auth, volunteers, guests, checkin, analytics, health
│   │   ├── auth_utils.py        # auth decorators + event-scope helper
│   │   └── middleware.py        # request IDs, security headers, error handling
│   ├── tests/                   # pytest + hypothesis (61 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # React SPA
│   └── src/
│       ├── pages/               # login, setup, dashboard, guests, check-in, analytics, volunteers
│       ├── services/            # api.ts (axios), endpoints.ts
│       └── context/             # AuthContext
├── infrastructure/cloudformation/
│   ├── vpc.yaml                 # VPC, subnets, 1 NAT gateway, security groups
│   ├── iam.yaml                 # ECS task roles, RDS monitoring role
│   ├── rds.yaml                 # MySQL 8.0 (single-AZ)
│   ├── alb.yaml                 # Application Load Balancer + target group
│   ├── ecs.yaml                 # Fargate cluster, task definition, service, autoscaling
│   └── cloudfront.yaml          # CloudFront + S3 bucket policy (OAC)
└── .kiro/specs/                 # requirements, design, and task breakdown
```

---

## How event scoping works

1. A **master** registers via **Setup**, choosing a new **2-digit event ID**
   (e.g. `42`). The ID must be unique — duplicates are rejected.
2. The master shares that event ID with their **volunteers**, who register into
   the **existing** event (joining a non-existent event is rejected).
3. Every user's session carries their `event_id`. Guest registration,
   check-in/out, dashboard, and analytics are all restricted to that event —
   users cannot see or modify another event's data.

---

## Core features

### Authentication
- Login by email or phone. A master account is created via **Setup**.
- **OTP is currently bypassed (demo mode)** — see Configuration below.
- Session tokens with expiry and revocation; role-based access control
  (master vs. volunteer).

### Guest management
- Register guests with contact, professional, emergency-contact, and
  event-specific details; 7 guest categories (General Attendee, VIP, Speaker,
  Staff, Volunteer, Press, Sponsor).
- Search by name (substring) or exact phone/email/ticket/badge.
- Phone numbers are stored canonically as `+CC-XXXXXXXXXX` and are immutable
  after registration.

### Check-in / check-out
- Volunteer-assisted check-in and check-out with duration tracking.
- Duplicate check-in detection with a re-check-in confirmation path.
- Rich confirmations: VIP/Speaker highlight, dietary/accessibility needs.

### Dashboard & analytics
- Live attendance metrics (present, departed, not-checked-in, peak) with
  polling.
- Breakdowns by category and location; capacity status; hourly check-in trends.

### Limits
- Max **200 total users** (masters + volunteers + guests) per deployment.
- Max **20 concurrent active sessions**.

---

## Running locally

### Backend
```bash
cd backend
pip install -r requirements.txt
copy .env.example .env     # defaults to a local SQLite DB
python wsgi.py             # http://localhost:5000/api/health
python -m pytest           # run the test suite
```
With no `DATABASE_URL`, the backend uses a local SQLite file and auto-creates
tables, so it runs without MySQL.

### Frontend
```bash
cd frontend
npm install
npm run dev                # http://localhost:5173  (proxied API via VITE_API_BASE_URL)
```

---

## Deployment

### Infrastructure (CloudFormation, deploy in order)
```
vpc → iam → rds → alb → ecs → cloudfront
```

### Backend
```bash
# build + push image
docker build --platform linux/amd64 -t event-tracker-backend:latest backend/
docker tag event-tracker-backend:latest <acct>.dkr.ecr.us-east-1.amazonaws.com/event-tracker-backend:latest
docker push <acct>.dkr.ecr.us-east-1.amazonaws.com/event-tracker-backend:latest
# roll out
aws ecs update-service --cluster event-tracker-cluster --service event-tracker-service --force-new-deployment
```

### Frontend
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://event-tracker-frontend-<acct>/ --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

---

## Configuration

Key environment variables (set on the ECS task definition, values from
Secrets Manager where sensitive):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | MySQL connection string (from Secrets Manager) |
| `AUTH_BYPASS_OTP` | `true` = skip OTP, auto-approve volunteers (demo). Set `false` for real auth. |
| `MAX_TOTAL_USERS` | Total-user cap (default `200`) |
| `MAX_CONCURRENT_SESSIONS` | Active-session cap (default `20`) |
| `AUTO_CREATE_TABLES` | Create tables on startup when `true` |
| `RESET_SCHEMA` | **Destructive** — drops & recreates all tables when `true`. Keep `false`. |
| `CLOUDWATCH_LOG_GROUP` | Log group for app logs |

OTP delivery (when `AUTH_BYPASS_OTP=false`) uses Twilio (SMS) and SendGrid
(email); provide their keys in the `event-tracker/prod` secret.

---

## Testing

```bash
cd backend
python -m pytest --cov=app
```
- **61 tests**, ~84% coverage.
- Includes property-based tests (Hypothesis) for phone normalization, OTP
  round-trip, check-in concurrency, duration accuracy, and data persistence,
  plus integration and security (RBAC, session, SQL-injection) tests.

---

## Known limitations

- **Demo auth**: OTP is bypassed and anyone can create a master or volunteer.
  Not production-safe until `AUTH_BYPASS_OTP=false` and real OTP delivery are
  enabled.
- **CloudFront masks API 403/404**: the SPA fallback (403/404 → `index.html`)
  also applies to `/api/*`, so API 403/404 responses can surface as the SPA page
  in the browser. Data scoping is still enforced server-side; this only affects
  how those two error codes are surfaced. Fix pending (scope the SPA fallback to
  the S3 origin only).
- **No data export** (CSV/Excel/PDF) and **no natural-language query** feature —
  these were descoped.
- **Single-AZ RDS** and a **single NAT gateway** — cost-optimized for a demo,
  not highly available.
- **No CI/CD pipeline** — builds and deploys are run manually.

---

## License

Developed for demonstration purposes.
