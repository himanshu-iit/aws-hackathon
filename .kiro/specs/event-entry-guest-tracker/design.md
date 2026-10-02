# Event Entry Guest Tracker System - Technical Design Document

## Overview

The Event Entry Guest Tracker System is a comprehensive AWS-native platform for managing guest registration, check-in/check-out operations, real-time attendance monitoring, analytics, and natural language query interfaces for events of all sizes. The system enforces a volunteer-assisted model where all guest interactions are mediated by approved volunteers, ensuring security, accuracy, and accountability.

### Key Design Principles

- **Volunteer-Mediated**: All guest-facing operations require volunteer assistance; guests cannot perform self-service operations
- **Real-Time Accuracy**: Immediate persistence of check-in/check-out events with sub-500ms latency requirements
- **Scalability**: Support for unlimited concurrent guests and simultaneous multi-volunteer operations via AWS auto-scaling
- **Data Integrity**: Transactional consistency across concurrent operations with audit trail enforcement via MySQL RDS
- **Security First**: OTP-based authentication, role-based access control, PII handling, and comprehensive AWS CloudWatch logging
- **Flexibility**: Optional guest identification methods and unlimited batch registration
- **Cloud-Native**: Serverless-friendly architecture leveraging AWS managed services

---

## Architecture

### High-Level System Architecture (AWS-Based)

```
┌────────────────────────────────────────────────────────────────┐
│                     CloudFront CDN                              │
│                  (Static Asset Distribution)                    │
└────────────────────────────────────────────────────────────────┘
                           │
┌────────────────────────────────────────────────────────────────┐
│                  S3 Static Website Hosting                       │
│             (React.js SPA - Single Page Application)            │
│    Master UI │ Volunteer UI │ Analytics │ Query Interface      │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│            Application Load Balancer (ALB)                       │
│         (HTTPS Termination, Request Routing)                    │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│              ECS Fargate Cluster (Flask Backend)                │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│   Task 1     │   Task 2     │   Task 3     │   Task N         │
│   (Flask)    │   (Flask)    │   (Flask)    │   (Flask)        │
└──────────────┴──────────────┴──────────────┴──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ MySQL RDS        │ │ AWS CloudWatch   │ │ AWS CloudWatch   │
│ (Primary DB)     │ │ (Logs)           │ │ (Metrics)        │
├──────────────────┤ └──────────────────┘ └──────────────────┘
│ Connection Pool  │
│ (SQLAlchemy)     │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ Audit Log Table  │
│ (Immutable Log)  │
└──────────────────┘
```

### Infrastructure as Code (CloudFormation)

```
CloudFormation Stacks
├── vpc-stack
│   ├── VPC (10.0.0.0/16)
│   ├── Public Subnets (multi-AZ)
│   ├── Private Subnets (multi-AZ)
│   ├── NAT Gateways
│   └── Route Tables
│
├── rds-stack
│   ├── MySQL 8.0 RDS Instance
│   ├── DB Parameter Group
│   ├── Security Group
│   └── Enhanced Monitoring IAM Role
│
├── ecs-stack
│   ├── ECS Cluster
│   ├── ECS Task Definition (Flask)
│   ├── ECS Service (auto-scaling)
│   ├── CloudWatch Log Group
│   └── CloudWatch Alarms
│
├── alb-stack
│   ├── Application Load Balancer
│   ├── Target Group
│   ├── Security Group
│   └── HTTPS Listener (ACM Certificate)
│
├── s3-stack
│   ├── S3 Bucket (Frontend)
│   ├── Bucket Policy (Public Read)
│   ├── Bucket Versioning
│   └── Server-Side Encryption
│
├── cloudfront-stack
│   ├── CloudFront Distribution
│   ├── Origin (S3 Bucket)
│   ├── Behaviors (Caching, TTL)
│   └── ACM Certificate (SSL/TLS)
│
└── iam-stack
    ├── ECS Task Execution Role
    ├── ECS Task Role (App permissions)
    ├── ECR Repository Policy
    └── CloudWatch Logs Role
```

### Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **React.js Frontend** | User interface (React components, routing, state management with Context API) |
| **CloudFront CDN** | Static asset distribution, caching, geographic proximity |
| **S3 Bucket** | Storage of React.js SPA assets (HTML, CSS, JS, images) |
| **ALB** | HTTPS termination, request routing to ECS tasks, health checks |
| **Flask Backend (ECS Fargate)** | Business logic, API endpoints, request processing |
| **SQLAlchemy ORM** | Object-relational mapping, query building, connection pooling |
| **MySQL RDS** | Primary relational database, ACID transactions, multi-AZ failover |
| **CloudWatch Logs** | Centralized logging from all components (ECS tasks, Lambda, etc.) |
| **CloudWatch Metrics** | Performance monitoring, auto-scaling triggers, alarms |
| **ECR** | Docker container image registry and versioning |
| **IAM Roles & Policies** | Fine-grained access control for AWS services |

---

## Technology Stack

### Frontend (S3 + CloudFront)

**Framework**: React.js (Single Page Application)
- Component-based UI architecture
- React Router for client-side navigation
- Context API or Redux for state management
- Axios or Fetch API for HTTP requests
- CORS configuration for cross-origin requests to ALB

**Static Assets**:
- HTML entry point
- CSS/SASS stylesheets
- JavaScript bundles (transpiled from JSX)
- Images and media files
- Service Worker for offline support (optional)

**Deployment**:
- Build: `npm run build` → outputs `/build` directory
- Upload: AWS CLI `s3 sync` command
- CloudFront: Invalidate cache on deployment (`/*` pattern)
- Version strategy: Append hash to filenames for cache-busting

**CDN Configuration**:
- Default TTL: 86400 seconds (1 day) for versioned assets
- HTML TTL: 0 seconds (always fresh) or 300 seconds (5 minutes)
- Geo-restriction: Optional based on event location

### Backend (ECS Fargate + Flask)

**Framework**: Python Flask
- Lightweight WSGI application framework
- Blueprints for modular route organization
- Request/response handling with JSON serialization

**Core Dependencies**:
- `Flask`: Web framework
- `Flask-SQLAlchemy`: ORM and connection pooling
- `Flask-CORS`: Cross-Origin Resource Sharing
- `Boto3`: AWS SDK for Python (CloudWatch, S3, CloudFormation interaction)
- `Flask-Marshmallow`: JSON serialization/deserialization
- `python-dotenv`: Environment configuration loading
- `requests`: HTTP client for external API calls (LLM, SMS/Email services)
- `UUID`: Unique identifier generation
- `datetime`: Timestamp handling
- `logging`: Python standard logging to CloudWatch

**API Endpoints** (REST Architecture):

```
Authentication Endpoints:
  POST   /api/auth/otp-request              - Request OTP
  POST   /api/auth/otp-verify               - Verify OTP code
  POST   /api/auth/master-setup             - Initial master user setup
  POST   /api/auth/logout                   - Revoke session token

Guest Management Endpoints:
  POST   /api/guests                        - Register single guest
  GET    /api/guests/{guest_id}             - Retrieve guest
  PUT    /api/guests/{guest_id}             - Update guest
  GET    /api/guests/search                 - Search guests
  DELETE /api/guests/{guest_id}             - Delete guest (master only)

Check-In/Check-Out Endpoints:
  POST   /api/events/{event_id}/check-in    - Check-in guest
  POST   /api/events/{event_id}/check-out   - Check-out guest
  GET    /api/events/{event_id}/status      - Get guest current status

Location Endpoints:
  POST   /api/events/{event_id}/locations   - Create location
  GET    /api/events/{event_id}/locations   - List locations
  GET    /api/events/{event_id}/locations/{location_id} - Get location

Dashboard Endpoints:
  GET    /api/events/{event_id}/dashboard   - Current attendance metrics
  GET    /api/events/{event_id}/attendance  - Detailed attendance data
  GET    /api/events/{event_id}/capacity    - Capacity status

Analytics Endpoints:
  GET    /api/events/{event_id}/analytics   - Generate report

Query Endpoints:
  POST   /api/queries                       - Process natural language query
  GET    /api/queries/history               - Query audit history

Volunteer Management Endpoints:
  POST   /api/volunteers/register           - Register new volunteer
  GET    /api/volunteers                    - List volunteers (master only)
  PUT    /api/volunteers/{volunteer_id}/approve - Approve volunteer
  DELETE /api/volunteers/{volunteer_id}/reject - Reject volunteer
```

**CORS Configuration**:
```python
# Allow requests from CloudFront distribution
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://distribution.cloudfront.net"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

**Request/Response Format** (JSON):

```json
// Request Example
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-5551234567",
  "category": "General_Attendee"
}

// Success Response
{
  "success": true,
  "data": {
    "guest_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z"
  }
}

// Error Response
{
  "success": false,
  "error": {
    "code": "INVALID_PHONE_FORMAT",
    "message": "Phone number must be in format +CC-XXXXXXXXXX",
    "details": { "provided": "+15551234567" }
  }
}
```

**Container Configuration** (Dockerfile):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

**ECS Task Definition** (Fargate):
- CPU: 256 units (0.25 vCPU) to 1024 units (1 vCPU)
- Memory: 512 MB to 3 GB
- Container port: 5000 (Flask default)
- Environment variables: Injected from AWS Secrets Manager
- Log configuration: CloudWatch Logs group `/ecs/event-tracker-app`
- Auto-scaling: Target tracking (CPU 70%, Memory 80%)

### Database (MySQL RDS)

**MySQL Version**: 8.0 (latest stable)

**Configuration**:
- Multi-AZ deployment for high availability
- Automated backups (30-day retention)
- Enhanced monitoring enabled
- Performance Insights enabled
- Encryption at rest (AWS KMS)
- Encryption in transit (SSL/TLS)

**Connection Pooling** (SQLAlchemy):

```python
engine = create_engine(
    'mysql+pymysql://user:password@rds-endpoint:3306/event_db',
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connection health
    pool_recycle=3600    # Recycle connections after 1 hour
)
```

**Schema**:
- Foreign key constraints enabled
- Indexes on frequently queried columns (guest_id, event_id, phone, email)
- Partitioning on check_in/check_out tables by event_id for large-scale events
- JSON columns for flexible metadata storage

**Backup Strategy**:
- Automated daily snapshots
- 30-day retention policy
- Cross-region replication (optional, for disaster recovery)
- Manual snapshots before major operations

### Logging (AWS CloudWatch)

**Log Sources**:
- Flask application logs (INFO, WARNING, ERROR levels)
- ECS Fargate container stdout/stderr
- ALB access logs (request/response details)
- MySQL RDS error log (connection issues, slow queries)

**Log Configuration**:

```python
import logging
import boto3
from pythonjsonlogger import jsonlogger

# CloudWatch Logs client
logs_client = boto3.client('logs', region_name='us-east-1')

# JSON logging for structured analysis
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Centralized logging
logger.info("Check-in event recorded", extra={
    "event_id": event_id,
    "guest_id": guest_id,
    "timestamp": datetime.utcnow().isoformat(),
    "volunteer_id": volunteer_id
})
```

**Log Groups**:
- `/ecs/event-tracker-app` - Application logs
- `/alb/event-tracker-alb` - Load balancer access logs
- `/rds/event-tracker-db` - Database error logs
- `/audit/event-tracker` - Audit trail logs

**Log Retention**: 30 days default (configurable per log group)

**CloudWatch Insights** (Ad-hoc queries):

```
fields @timestamp, @message, event_id, guest_id
| filter level = "ERROR"
| stats count() as error_count by event_id
```

### Deployment Automation

**Infrastructure Deployment**:

```bash
#!/bin/bash
# Deploy CloudFormation stacks

aws cloudformation create-stack \
  --stack-name event-tracker-vpc \
  --template-body file://vpc.yaml \
  --region us-east-1

aws cloudformation create-stack \
  --stack-name event-tracker-rds \
  --template-body file://rds.yaml \
  --parameters ParameterKey=VPCStack,ParameterValue=event-tracker-vpc \
  --region us-east-1

aws cloudformation create-stack \
  --stack-name event-tracker-ecs \
  --template-body file://ecs.yaml \
  --region us-east-1
```

**Container Image Deployment**:

```bash
#!/bin/bash
# Build and push Docker image to ECR

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URL="$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/event-tracker-app"

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO_URL

# Build image
docker build -t event-tracker-app:latest .
docker tag event-tracker-app:latest $ECR_REPO_URL:latest
docker tag event-tracker-app:latest $ECR_REPO_URL:$(git rev-parse --short HEAD)

# Push to ECR
docker push $ECR_REPO_URL:latest
docker push $ECR_REPO_URL:$(git rev-parse --short HEAD)

# Update ECS service to new image
aws ecs update-service \
  --cluster event-tracker-cluster \
  --service event-tracker-service \
  --force-new-deployment \
  --region us-east-1
```

**Frontend Deployment**:

```bash
#!/bin/bash
# Build and deploy React.js SPA to S3 + CloudFront

# Build React app
npm install
npm run build

# Sync to S3
aws s3 sync build/ s3://event-tracker-frontend-bucket/ \
  --delete \
  --cache-control "max-age=31536000" \
  --region us-east-1

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234ABCD5678 \
  --paths "/*" \
  --region us-east-1
```

**CI/CD Pipeline** (AWS CodePipeline):
- Source: GitHub/CodeCommit
- Build: CodeBuild (Docker image build, tests)
- Deploy: CloudFormation for infrastructure, CodeDeploy for ECS
- Approval: Manual gate before production deployment

### Auto-Scaling Configuration

**ECS Task Auto-Scaling**:

```
Target Tracking Policy:
- Target Metric: Average CPU Utilization
- Target Value: 70%
- Scale-out cooldown: 60 seconds
- Scale-in cooldown: 300 seconds

Task Count:
- Minimum: 1 tasks (high availability)
- Maximum: 2 tasks (cost control)
- Desired: 1 tasks (baseline)
```

**RDS Auto-Scaling** (Storage):
- Storage auto-scaling enabled
- Maximum allocated storage: 10 GB
- Threshold: 80% utilization

---

## Data Models

### Core Entity Models (SQLAlchemy ORM)

#### User Hierarchy

```python
# Base User class
class User(db.Model):
    user_id = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20))
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }

# Master User
class MasterUser(User):
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    __mapper_args__ = {
        'polymorphic_identity': 'master_user'
    }

# Volunteer
class Volunteer(User):
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.Enum('pending_approval', 'approved', 'rejected'),
        default='pending_approval'
    )
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'volunteer'
    }

# Guest
class Guest(db.Model):
    guest_id = db.Column(db.String(36), primary_key=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.event_id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    company = db.Column(db.String(255), nullable=True)
    job_title = db.Column(db.String(255), nullable=True)
    profession = db.Column(db.String(255), nullable=True)
    emergency_contact_name = db.Column(db.String(255), nullable=False)
    emergency_contact_phone = db.Column(db.String(20), nullable=False)
    ticket_number = db.Column(db.String(100), nullable=True, unique=True, index=True)
    badge_number = db.Column(db.String(100), nullable=True, unique=True, index=True)
    category = db.Column(
        db.Enum('General_Attendee', 'VIP', 'Speaker', 'Staff', 'Volunteer', 'Press', 'Sponsor'),
        default='General_Attendee',
        index=True
    )
    dietary_restrictions = db.Column(db.String(500), nullable=True)
    accessibility_needs = db.Column(db.String(500), nullable=True)
    current_status = db.Column(
        db.Enum('present', 'departed', 'not_checked_in'),
        default='checked_in',
        index=True
    )
    current_location = db.Column(db.String(100), nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    registered_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    metadata = db.Column(db.JSON, nullable=True)
    
    # Relationships
    check_in_events = db.relationship('CheckInEvent', backref='guest', cascade='all, delete-orphan')
    check_out_events = db.relationship('CheckOutEvent', backref='guest', cascade='all, delete-orphan')
```

#### Event Models

```python
class Event(db.Model):
    event_id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    settings = db.Column(db.JSON, nullable=True)
    
    # Relationships
    locations = db.relationship('LocationIdentifier', backref='event', cascade='all, delete-orphan')
    guests = db.relationship('Guest', backref='event', cascade='all, delete-orphan')


class LocationIdentifier(db.Model):
    location_id = db.Column(db.String(100), primary_key=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.event_id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    location_type = db.Column(
        db.Enum('entrance', 'exit', 'other'),
        default='other',
        nullable=False
    )
    __table_args__ = (db.UniqueConstraint('event_id', 'location_id', name='unique_location_per_event'),)
```

#### Attendance Tracking Models

```python
class CheckInEvent(db.Model):
    __tablename__ = 'check_in_event'
    checkin_id = db.Column(db.String(36), primary_key=True)
    guest_id = db.Column(db.String(36), db.ForeignKey('guest.guest_id'), nullable=False, index=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.event_id'), nullable=False, index=True)
   timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    location_id = db.Column(db.String(100), nullable=False)
    volunteer_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    badge_scan = db.Column(db.Boolean, default=False)
    ticket_scan = db.Column(db.Boolean, default=False)
    name_search = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(500), nullable=True)
    
    # Composite index for efficient querying
    __table_args__ = (
        db.Index('idx_guest_event_time', 'guest_id', 'event_id', 'timestamp'),
    )

class CheckOutEvent(db.Model):
    __tablename__ = 'check_out_event'
    checkout_id = db.Column(db.String(36), primary_key=True)
    guest_id = db.Column(db.String(36), db.ForeignKey('guest.guest_id'), nullable=False, index=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.event_id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    location_id = db.Column(db.String(100), nullable=False)
    volunteer_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    
    __table_args__ = (
        db.Index('idx_guest_event_time', 'guest_id', 'event_id', 'timestamp'),
    )

```

#### Authentication Models

```python
class OTPRequest(db.Model):
    otp_id = db.Column(db.String(36), primary_key=True)
    phone_or_email = db.Column(db.String(255), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    request_type = db.Column(
        db.Enum('master_setup', 'master_login', 'volunteer_registration', 'volunteer_login'),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempt_count = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime, nullable=True)

```

#### Audit and Logging Models

```python
class AuditLog(db.Model):
    log_id = db.Column(db.String(36), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    action_type = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.String(36), nullable=False)
    changes = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.Enum('success', 'failure'), nullable=False)
    error_message = db.Column(db.String(500), nullable=True)

class QueryLog(db.Model):
    query_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False, index=True)
    query_text = db.Column(db.Text, nullable=False)
    query_hash = db.Column(db.String(64), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    response = db.Column(db.Text, nullable=False)
    data_accessed = db.Column(db.JSON, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: OTP Validation Round Trip

*For any* valid phone number or email provided during authentication, generating an OTP and then verifying it with the correct code should result in a valid authenticated event, while an incorrect code should be rejected.

**Validates: Requirements 1.5-1.8, 2.4-2.7**

### Property 2: Phone Number Normalization Idempotence

*For any* phone number with country code, normalizing it to +CC-XXXXXXXXXX format and then normalizing the result again should produce an identical output.

**Validates: Requirements 3.1-3.5**

### Property 3: Volunteer Status Transitions

*For any* approved volunteer, once their status changes from "pending_approval" to "approved", subsequent login attempts using their phone number should succeed with volunteer permissions granted.

**Validates: Requirements 5.6-5.7, 6.1-6.3**

### Property 4: Guest Registration Persistence

*For any* guest registration with complete required fields, persisting the guest data to RDS and then retrieving it by guest_id should return identical information (excluding auto-generated fields like timestamps).

**Validates: Requirement 7.1-7.9**

### Property 5: Check-In Creates Concurrent-Safe Records

*For any* collection of simultaneous check-in requests for distinct guests, the system should create exactly N distinct Check_In records without race conditions or data loss, where N is the number of requests.

**Validates: Requirements 9.7, 21.1, 21.3**

### Property 6: Check-Out Requires Active Check-In

*For any* guest who has not checked in or has already checked out, attempting checkout should fail; only guests with an active check-in should be able to check out successfully.

**Validates: Requirements 10.10-10.11, 22.3-22.4**

### Property 7: Duration Calculation Accuracy

*For any* check-in at time T1 and checkout at time T2 where T2 > T1, the calculated duration should equal (T2 - T1) in minutes.

**Validates: Requirements 10.8, 12.4**

### Property 8: Attendance Data Consistency

*For any* query of current attendance statistics, the sum of (currently_present + checked_out + not_checked_in) should equal the total number of registered guests at that moment.

**Validates: Requirement 21.5**

### Property 9: Natural Language Query Access Control

*For any* volunteer user executing a natural language query, the results returned should only include data from events where that volunteer is authorized; attempting to query unauthorized events should return empty or access-denied results.

**Validates: Requirements 18.2-18.4**

### Property 10: Audit Trail Immutability

*For any* audit log entry created in CloudWatch and RDS, querying the audit log by log_id should return the exact same entry unchanged; no modifications should be permitted to audit records.

**Validates: Requirement 20.3-20.4**

### Property 11: Data Persistence Across Restarts

*For any* guest, check-in,or  check-out before an ECS task restart or RDS failover, querying for these entities should return the identical data that was present before restart (multi-AZ ensures availability).

**Validates: Requirement 24.1-24.3**

### Property 12: Batch Registration Atomicity

*For any* batch registration request with N valid guests, either all N guests are created with consistent IDs and timestamps in RDS, or the entire batch fails and no guests are created (no partial registrations).

**Validates: Requirement 7.10**

### Property 13: Capacity Monitoring Consistency

*For any* event with configured capacity C and current check-in count P, the dashboard capacity status should show "critical" if and only if P ≥ C, "warning" if 0.8C ≤ P < C, and "normal" otherwise.

**Validates: Requirements 23.2-23.3**

---

## Data Flow and Key Scenarios

### First-Time Setup Flow

```
React.js Frontend Loads
     ↓
Detects Empty RDS Database
     ↓
Displays Master User Creation UI
     ↓
User Enters Email + Phone (with Country Code)
     ↓
POST /api/auth/otp-request → Flask Backend
     ↓
Generate OTP (6 digits) → Store in RDS with 5-minute TTL
     ↓
Send OTP via SMS (Twilio) + Email (SendGrid)
     ↓
User Verifies any of the OTPs
     ↓
POST /api/auth/master-setup → Flask Backend
     ↓
Verify Both OTPs in RDS
     ↓
Create MasterUser record in RDS
     ↓
Generate Session Token → Return to Frontend
     ↓
Frontend Stores Token (localStorage or sessionStorage)
     ↓
Redirect to Dashboard
     ↓
Log audit event to CloudWatch and RDS
```

### Guest Check-In Flow (Concurrent-Safe with RDS Transactions)

```
Volunteer Opens React.js Frontend
     ↓
Volunteer Identifies Guest (name search, badge scan, or ticket number)
     ↓
Frontend sends: GET /api/guests/search?name=John
     ↓
Flask queries RDS via SQLAlchemy
     ↓
Returns Guest record
     ↓
Volunteer Selects Location
     ↓
POST /api/events/{event_id}/check-in → Flask Backend
     ↓
Flask begins RDS transaction (ACID guarantees)
     ↓
Validate: Guest exists in RDS
     ↓
Validate: Location exists in RDS
     ↓
Validate: Guest not already checked in (no active check-in record)
     ↓
Create CheckInEvent record in RDS
     ↓
Update Guest.current_status = "present" in RDS
     ↓
Commit transaction
     ↓
Log to CloudWatch (JSON structured logs)
     ↓
Log audit event to RDS
     ↓
Publish update to all connected React frontends (WebSocket or polling)
     ↓
Frontend displays: "Guest X checked in at Y"
```

### Natural Language Query Flow

```
Volunteer Enters Question: "How many guests are currently in the venue?"
     ↓
Frontend sends: POST /api/queries { query: "How many..." }
     ↓
Flask NLQueryProcessor receives request
     ↓
Hash query for potential cache key
     ↓
Check local in-memory cache (5-minute TTL)
     ├─ Cache Hit → Return cached result immediately
     └─ Cache Miss → Continue
     ↓
Send query to LLM API (OpenAI GPT-4 or Claude)
     ↓
LLM interprets: { intent: 'COUNT_CURRENT_ATTENDEES', filters: [] }
     ↓
Apply role-based access control (Volunteer can only query events they're assigned to)
     ↓
Execute SQL query: SELECT COUNT(*) FROM guest WHERE event_id=X AND current_status='present'
     ↓
SQLAlchemy ORM translates to SQL and executes on RDS
     ↓
Aggregate result (no PII sent to LLM)
     ↓
Send result back to LLM for response generation
     ↓
LLM returns: "Currently, 347 guests are in the venue."
     ↓
Cache result for 5 minutes
     ↓
Log query and result to QueryLog table in RDS
     ↓
Log to CloudWatch for monitoring
     ↓
Return response to React frontend
     ↓
Frontend displays answer to Volunteer
```

---

## Error Handling and Validation

### Authentication Errors

| Error Scenario | Handling Strategy |
|---|---|
| Invalid phone format (not 10 digits + CC) | 400 Bad Request; display format requirement in React |
| OTP expired (>5 minutes) | 401 Unauthorized; allow user to request new OTP |
| Incorrect OTP (3 attempts) | 429 Too Many Requests; block login for 15 minutes; log to CloudWatch |
| Email/phone mismatch during setup | 400 Bad Request; require both to match saved values in RDS |
| Duplicate Master_User email/phone | 409 Conflict; indicate already registered in response |
| Volunteer not approved | 403 Forbidden; display pending status |

### Guest Management Errors

| Error Scenario | Handling Strategy |
|---|---|
| Required guest fields missing | 400 Bad Request; highlight missing fields in React form validation |
| Invalid phone format in batch | 400 Bad Request; return problematic record index and reason |
| Duplicate ticket/badge numbers | 409 Conflict; warn volunteer in UI; allow override with confirmation |
| Non-existent guest on check-in | 404 Not Found; suggest searching again via React search UI |
| Location does not exist | 400 Bad Request; display available locations from RDS query |

### Database and Concurrency Errors

| Error Scenario | Handling Strategy |
|---|---|
| RDS connection pool exhausted | 503 Service Unavailable; log to CloudWatch; auto-retry with exponential backoff |
| Race condition during check-in | 409 Conflict; SQLAlchemy retry logic or optimistic locking via version field |
| Simultaneous check-out of same guest | Last write wins (timestamp in RDS); audit both attempts in AuditLog |
| Capacity exceeded | Warn volunteer in React UI; allow override with Master_User approval |
| Transaction timeout (>120 seconds) | 504 Gateway Timeout; rollback RDS transaction; log to CloudWatch |

---

## Testing Strategy

### Unit Testing (pytest)

**Scope**: Individual service methods and business logic

- Flask route handlers (status codes, response format)
- SQLAlchemy ORM queries and model validations
- Phone number normalization and validation
- Guest data validation (required fields, formats)
- Location validation queries
- Duration calculations

**Example Tests**:
```python
def test_normalize_phone_idempotent():
    """Phone normalization is idempotent"""
    phone1 = normalize_phone("+1-5551234567")
    phone2 = normalize_phone(phone1)
    assert phone1 == phone2

def test_check_out_without_check_in_fails(client, db):
    """Checkout blocked for non-checked-in guests"""
    response = client.post(f'/api/events/{event_id}/check-out', 
                          json={'guest_id': guest_id})
    assert response.status_code == 409

def test_capacity_warning_at_80_percent():
    """Capacity status is warning at exactly 80% utilization"""
    assert get_capacity_status(capacity=100, current=80) == 'warning'
```

### Property-Based Testing (Hypothesis)

**Scope**: Universal properties that should hold across all inputs

**Property 1: OTP Validation Round Trip**
- Generate OTP with valid phone/email → Verify with correct code → Should succeed
- 100+ iterations with randomized valid phone numbers (+1, +44, +91, etc.) and email addresses

**Property 2: Check-In Concurrency Safety**
- 50 concurrent check-in requests for 50 distinct guests → Exactly 50 CheckInEvent records in RDS
- No race conditions, no data loss, no duplicate records
- Repeats 20 times with different concurrency patterns

**Property 3: Attendance Consistency**
- For any event state: sum(present, departed, not_checked_in) == total_registered
- Runs after every check-in/check-out operation; 1000+ state transitions

**Property 4: Guest Data Persistence**
- Register guest with random valid data → Query RDS by guest_id → Identical data returned
- 100+ iterations with varying guest categories, companies, professions

**Property 5: Dashboard Latency**
- For any new check-in event → Dashboard update via HTTP polling arrives within 5 seconds
- Measured from RDS write to frontend display
- 50+ iterations with varying load patterns

### Integration Testing

**Scope**: End-to-end workflows with multiple components

- Full setup flow (Master_User creation → RDS persistence → first login)
- Volunteer registration → Master_User approval in RDS → Volunteer login
- Complete event workflow (register guests → check-in → check-out → generate reports)
- Natural language query with various question types
- Concurrent multi-volunteer check-in/check-out
- Data export in all formats (CSV, JSON, Excel, PDF)
- CloudWatch log verification for all operations

### Performance and Load Testing

- 1000+ concurrent Flask requests (ECS auto-scaling verification)
- RDS connection pool stress (verify max_overflow=40 handles burst)
- ALB distribution across multiple ECS tasks
- S3 + CloudFront latency for React.js SPA
- MySQL RDS query performance (indexed lookups under 100ms)
- Auto-scaling triggers and scale-down behavior

### Security Testing

- OTP brute force (verify 15-minute lockout after 3 attempts)
- Session token expiration and revocation
- Role-based access control (Volunteer cannot approve other Volunteers)
- PII handling in LLM queries (no personal identifiers sent)
- CloudWatch logs contain no sensitive data
- CORS configuration allows only CloudFront origin
- IAM role permissions follow principle of least privilege

---

## Deployment Architecture

### CloudFormation Templates Structure

```
templates/
├── vpc.yaml                  # VPC, Subnets, NAT Gateways, Route Tables
├── rds.yaml                  # MySQL RDS instance, Multi-AZ, Security Group
├── ecs.yaml                  # ECS Cluster, Task Definition, Service, Auto-Scaling
├── alb.yaml                  # Application Load Balancer, Target Groups, Listeners
├── s3.yaml                   # S3 bucket, bucket policy, versioning, encryption
├── cloudfront.yaml           # CloudFront distribution, behaviors, ACM certificate
├── iam.yaml                  # IAM roles, task execution role, task role
├── cloudwatch.yaml           # Log groups, alarms, metrics, dashboards
└── main.yaml                 # Master stack that orchestrates all others
```

### Deployment Checklist

- [x] Create VPC and networking infrastructure (CloudFormation)
- [x] Create RDS MySQL 8.0 instance with Multi-AZ
- [x] Create ECR repository for Docker images
- [x] Create S3 bucket for React.js frontend
- [x] Create CloudFront distribution pointing to S3
- [x] Create ALB with HTTPS listener
- [x] Create ECS cluster, task definition, and service
- [x] Configure auto-scaling for ECS tasks
- [x] Set up CloudWatch log groups and metrics
- [x] Configure IAM roles with least privilege
- [x] Generate SSL/TLS certificates (AWS Certificate Manager)
- [x] Configure CORS on Flask backend
- [x] Test full deployment with smoke tests
- [x] Configure backup and disaster recovery

### Environment Configuration (AWS Secrets Manager)

```yaml
event-tracker/prod:
  DATABASE_URL: mysql+pymysql://user:password@rds-endpoint:3306/event_db
  FLASK_ENV: production
  FLASK_DEBUG: false
  LOG_LEVEL: INFO
  CORS_ORIGINS: https://distribution.cloudfront.net
  OTP_TTL_MINUTES: 5
  OTP_RETRY_LIMIT: 3
  LLM_API_KEY: sk-...
  TWILIO_API_KEY: ...
  SENDGRID_API_KEY: ...
  AWS_REGION: us-east-1
  CLOUDWATCH_LOG_GROUP: /ecs/event-tracker-app
```

---

## Security Considerations

1. **OTP Security**: 6-digit OTP with 5-minute TTL, 3-retry lockout, rate limiting (5 per hour per phone), stored in RDS
2. **PII Protection**: Natural language queries use only aggregated/anonymized data; no personal identifiers sent to LLM
3. **Database Encryption**: MySQL RDS with encryption at rest (AWS KMS) and in transit (SSL/TLS)
4. **Access Control**: Role-based (Master_User, Volunteer); IAM roles follow principle of least privilege
5. **Audit Trail**: Immutable append-only AuditLog table in RDS + CloudWatch logs for all user actions
6. **CloudFront Security**: Origin access identity (OAI) restricts S3 access; only CloudFront can serve content
7. **ALB Security**: HTTPS termination with ACM certificate; security group allows only necessary ports
8. **ECS Security**: Task execution role limited to ECR pull; task role limited to RDS access, CloudWatch logs
9. **Input Validation**: All user inputs validated in Flask before processing (phone format, guest data, location identifiers)

---

## Performance Targets

| Metric | Target | Implementation |
|---|---|---|
| Dashboard Load Latency | < 2 seconds | S3 + CloudFront caching, React.js SPA optimization |
| Dashboard Update Latency | < 5 seconds | HTTP polling or WebSocket from Flask backend |
| Check-In/Check-Out Persistence | < 500ms | RDS connection pooling, indexed queries |
| Query Response (cached) | < 500ms | Flask in-memory cache (5-minute TTL) |
| Query Response (cache miss) | < 3 seconds | LLM interpretation + SQLAlchemy ORM execution |
| OTP Delivery | < 1 minute | Twilio SMS + SendGrid Email |
| Concurrent Operations | 1000+ simultaneous | ECS auto-scaling, ALB distribution |
| Batch Registration | 100 guests/batch | RDS transaction atomicity |
| ECS Task Start | < 30 seconds | Fargate container cold start |
| RDS Query (indexed) | < 100ms | MySQL indexes on frequently queried columns |

---

## Known Constraints and Trade-offs

1. **Guest Identification Optional**: System supports guests identified by name search, badge number, or ticket number; no biometric or RFID required
2. **Volunteer-Mediated**: All guest interactions require Volunteer assistance; increases operational overhead but ensures accountability
3. **Capacity Monitoring**: Location-based capacity is tracked but can be overridden by Master_User (hard limit enforcement optional)
4. **LLM Dependency**: Query interface depends on external LLM service availability; query caching helps mitigate latency
5. **Concurrent Operations**: High concurrency (1000+) may require ECS task scaling or distributed locking strategies
6. **No Redis Caching**: Simple in-memory Python cache used instead; for higher concurrency, consider ElastiCache Redis
7. **RDS Scalability**: Multi-AZ RDS provides HA but vertical scaling only; partitioning of check-in/check-out tables recommended for 1M+ records
8. **CloudFront Cost**: Higher latency regions may experience increased CloudFront costs due to data egress

---

## AWS Services Used

| Service | Purpose |
|---|---|
| **EC2 / ECS Fargate** | Container orchestration for Flask backend |
| **RDS MySQL** | Relational database (primary data store) |
| **S3** | Static website hosting (React.js SPA) |
| **CloudFront** | CDN for S3-hosted frontend |
| **Application Load Balancer** | Traffic distribution to ECS tasks |
| **CloudWatch** | Logs, metrics, alarms, dashboards |
| **CloudFormation** | Infrastructure as Code (IaC) |
| **Elastic Container Registry (ECR)** | Docker image repository |
| **AWS Secrets Manager** | Secure configuration storage |
| **Identity & Access Management (IAM)** | Fine-grained access control |
| **AWS Certificate Manager (ACM)** | SSL/TLS certificate management |
| **Auto Scaling** | Dynamic ECS task scaling |
| **VPC** | Networking isolation and security |

