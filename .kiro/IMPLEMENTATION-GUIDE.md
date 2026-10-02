# Event Entry Guest Tracker — Implementation Guide (As-Built)

This guide documents the system **as actually built and deployed**. For the
original planning artifacts see `.kiro/specs/event-entry-guest-tracker/`
(requirements, design, tasks).

**Live demo:** https://d2y60we8f8rlpl.cloudfront.net

---

## 1. Architecture (as deployed)

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

- CloudFront serves the React app from S3 and **proxies `/api/*` to the ALB**,
  so the browser is always same-origin HTTPS (no CORS, no mixed content).
- Flask runs as Fargate containers behind an ALB.
- MySQL on RDS stores all data; CloudWatch collects logs.
- No Redis / no caching layer — analytics query RDS directly.

### Stack
- **Frontend:** React 18 + TypeScript + Vite + React Router + Context API
- **Backend:** Python 3.11 + Flask + Flask-SQLAlchemy + Gunicorn
- **Database:** MySQL 8.0 on RDS (single-AZ)
- **Infra:** CloudFormation, ECS Fargate, ALB, S3, CloudFront, ECR, Secrets Manager

---

## 2. AWS resources (us-east-1, account 100611700941)

| Resource | Name / ID |
|----------|-----------|
| ECR repo | `event-tracker-backend` |
| Frontend bucket | `event-tracker-frontend-100611700941` |
| CFN templates bucket | `event-tracker-cfn-templates-100611700941` |
| ECS cluster / service | `event-tracker-cluster` / `event-tracker-service` |
| RDS instance | `event-tracker-db` (MySQL 8.0, single-AZ) |
| ALB DNS | `event-tracker-alb-187512089.us-east-1.elb.amazonaws.com` |
| CloudFront | distribution `E279XIX58XL6GT` → `d2y60we8f8rlpl.cloudfront.net` |
| Secret | `event-tracker/prod` (Secrets Manager) |
| Log group | `/ecs/event-tracker-app` |

### CloudFormation stacks (deploy order)
```
event-tracker-vpc → event-tracker-iam → event-tracker-rds
→ event-tracker-alb → event-tracker-ecs → event-tracker-cloudfront
```
Templates live in `infrastructure/cloudformation/`.

---

## 3. What was built, by phase

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | AWS infrastructure (VPC, RDS, ALB, ECS, S3/CloudFront, ECR, CloudWatch) | ✅ Deployed |
| 2 | Flask backend foundation (models, services, logging, middleware) | ✅ |
| 3 | React frontend foundation (routing, context, API client) | ✅ Deployed |
| 4 | Authentication APIs (OTP, master setup, login, volunteer approval) | ✅ (OTP bypass in demo) |
| 5 | Guest management (register, search, list, update, soft-delete) | ✅ |
| 6 | Check-in/check-out engine (locking, duration, duplicate detection) | ✅ |
| 7 | Real-time dashboard (metrics, category/location, capacity) | ✅ |
| 8 | Analytics & reporting (summary, hourly, sessions, categories, peak) | ✅ (export descoped) |
| 9 | Natural-language queries | ⏭ Skipped |
| 10 | Frontend components (all feature pages) | ✅ Deployed |
| 11 | Testing & verification (61 tests, ~84% coverage) | ✅ (CI/CD + docs tasks skipped) |

### Later enhancements beyond the original plan
- **OTP bypass mode** (`AUTH_BYPASS_OTP`) for open demo registration + auto-approved volunteers.
- **Capacity limits**: 200 total users, 20 concurrent sessions (ECS env-configurable).
- **Per-event scoping**: 2-digit event IDs; masters create an event, volunteers join an existing one, and all data is isolated per event.

---

## 4. Deploy / redeploy

**Backend**
```bash
docker build --platform linux/amd64 -t event-tracker-backend:latest backend/
docker tag  event-tracker-backend:latest 100611700941.dkr.ecr.us-east-1.amazonaws.com/event-tracker-backend:latest
docker push 100611700941.dkr.ecr.us-east-1.amazonaws.com/event-tracker-backend:latest
aws ecs update-service --cluster event-tracker-cluster --service event-tracker-service --force-new-deployment --region us-east-1
```

**Frontend**
```bash
cd frontend && npm run build
aws s3 sync dist/ s3://event-tracker-frontend-100611700941/ --delete --region us-east-1
aws cloudfront create-invalidation --distribution-id E279XIX58XL6GT --paths "/*"
```

**Infra change** — edit the template in `infrastructure/cloudformation/` and
`aws cloudformation update-stack ...`.

---

## 5. Key configuration (ECS task env)

| Variable | Default | Notes |
|----------|---------|-------|
| `AUTH_BYPASS_OTP` | `true` | Demo: skip OTP, auto-approve volunteers. Set `false` for real auth. |
| `MAX_TOTAL_USERS` | `200` | masters + volunteers + guests |
| `MAX_CONCURRENT_SESSIONS` | `20` | active sessions |
| `AUTO_CREATE_TABLES` | `true` | create tables on startup |
| `RESET_SCHEMA` | `false` | **destructive** full table reset; only used once to apply schema changes |

---

## 6. Known limitations

- **Demo auth** — OTP bypassed; anyone can create a master/volunteer. Not production-safe.
- **CloudFront masks API 403/404** — SPA fallback (403/404 → index.html) also
  applies to `/api/*`; server-side scoping is still enforced, only the surfaced
  error code is affected. Fix pending.
- **Descoped**: data export (CSV/Excel/PDF), natural-language queries, batch guest upload.
- **Not HA**: single-AZ RDS, single NAT gateway (cost-optimized for demo).
- **No CI/CD** — manual build/deploy.

---

## 7. Where to look

- Backend code: `backend/app/`
- Frontend code: `frontend/src/`
- Infra: `infrastructure/cloudformation/`
- Tests: `backend/tests/` (`python -m pytest`)
- Original spec: `.kiro/specs/event-entry-guest-tracker/`
