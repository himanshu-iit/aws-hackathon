# Event Entry Guest Tracker — Resource Index

A map of the project's documents and where to find things. For the as-built
system overview, start with `.kiro/IMPLEMENTATION-GUIDE.md`.

**Live demo:** https://d2y60we8f8rlpl.cloudfront.net

---

## Specification documents (`.kiro/specs/event-entry-guest-tracker/`)

| File | Purpose |
|------|---------|
| `requirements.md` | 25 functional requirements, user stories, EARS acceptance criteria, glossary |
| `design.md` | Technical design: AWS architecture (React + Flask + RDS + CloudWatch), SQLAlchemy models, REST API, correctness properties |
| `tasks.md` | Phased implementation plan (phases 1–11) |

> Note: the spec is the original plan. A few items were **descoped during
> implementation** — data export, natural-language queries (Phase 9), batch
> guest upload, and CI/CD. The spec text may still reference them.

---

## As-built guide

| File | Purpose |
|------|---------|
| `.kiro/IMPLEMENTATION-GUIDE.md` | **Start here** — what was actually built & deployed, AWS resources, deploy commands, config, known limitations |
| `README.md` (repo root) | Project overview, architecture, local dev, deployment |

---

## Source code

| Area | Path |
|------|------|
| Backend (Flask) | `backend/app/` — `models/`, `services/`, `blueprints/`, `factory.py`, `middleware.py`, `auth_utils.py` |
| Backend tests | `backend/tests/` — run `python -m pytest` (61 tests, ~84% coverage) |
| Frontend (React) | `frontend/src/` — `pages/`, `services/`, `context/` |
| Infrastructure | `infrastructure/cloudformation/` — `vpc`, `iam`, `rds`, `alb`, `ecs`, `cloudfront` templates |
| Workspace config | `settings.yaml` (project + AWS resource references) |

---

## Skills reference (`.kiro/skills/`)

Background learning material created during planning. Still useful as topic
references; the time estimates were planning guesses, not actuals.

- `aws-cloud-architecture.md` — VPC, RDS, ECS, ALB, S3/CloudFront, CloudFormation
- `python-flask-backend.md` — Flask, SQLAlchemy, REST APIs
- `react-frontend-development.md` — React, TypeScript, routing, state
- `docker-container-deployment.md` — Docker, ECR, ECS Fargate
- `database-design-mysql.md` — schema design, MySQL, pooling
- `api-design-rest.md` — REST principles, error handling
- `testing-quality-assurance.md` — pytest, Hypothesis, integration tests
- `devops-cicd-pipeline.md` — build/deploy automation (CI/CD not implemented)
- `llm-integration-nlp.md` — LLM integration (feature descoped)
- `security-authentication.md` — OTP, sessions, RBAC
- `skills-summary.md`, `SKILLS-INDEX.md` — overviews

---

## Quick reading order

1. `README.md` — what the system is
2. `.kiro/IMPLEMENTATION-GUIDE.md` — how it's built and deployed
3. `.kiro/specs/.../requirements.md` → `design.md` — the original intent
4. Source under `backend/`, `frontend/`, `infrastructure/`

---

## Current status (summary)

- Backend + frontend **deployed and live** on AWS.
- Phases 1–8, 10, 11 complete; Phase 9 (NL queries) skipped.
- Demo mode: OTP bypassed, open registration, per-event scoping (2-digit IDs).
- Known gaps: CloudFront masks API 403/404; no export/NL-query/CI-CD; single-AZ.
