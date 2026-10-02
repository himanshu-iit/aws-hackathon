# Implementation Plan: Event Entry Guest Tracker System

## Overview

This implementation plan breaks down the Event Entry Guest Tracker System into logical phases following a volunteer-assisted, real-time attendance tracking architecture. The system prioritizes data integrity, concurrent operation handling, and real-time analytics through a cloud-native AWS architecture with Python Flask backend, React.js frontend, MySQL RDS database, and CloudWatch logging. Implementation follows an 11-phase approach: infrastructure setup (CloudFormation, VPC, RDS, ECR), backend foundation (Flask, SQLAlchemy ORM, CloudWatch), frontend setup (React.js, S3, CloudFront), then feature implementation (authentication, guest management, check-in engine, real-time dashboard, analytics, NLP queries), and finally testing and deployment automation.

---

## Phase 1: AWS Infrastructure Setup

### Objective

Establish core AWS infrastructure, networking, MySQL RDS database, ECR container registry, S3/CloudFront, and ALB for the Event Entry Guest Tracker System.

---

- [ ] 1. VPC and Networking Infrastructure
  - Create CloudFormation template for VPC (10.0.0.0/16 CIDR)
  - Set up multi-AZ public subnets (for ALB, NAT Gateways)
  - Set up multi-AZ private subnets (for ECS Fargate, RDS)
  - Create NAT Gateways in public subnets for outbound internet access
  - Configure route tables (public and private)
  - Set up Internet Gateway for public subnet access
  - Create Security Groups: ALB (443, 80), ECS (5000 from ALB), RDS (3306 from ECS)
  - _Requirements: 25.1, 25.2_

- [ ] 2. MySQL RDS Database Setup
  - Create CloudFormation template for MySQL 8.0 RDS instance
  - Configure Multi-AZ deployment for high availability and automatic failover
  - Set up enhanced monitoring and Performance Insights
  - Configure encryption at rest (AWS KMS) and encryption in transit (SSL/TLS)
  - Set up automated backups (30-day retention)
  - Create security group allowing inbound traffic from ECS on port 3306
  - Set up parameter group for MySQL 8.0 with appropriate my.cnf configuration
  - Store database username/password in AWS Secrets Manager
  - _Requirements: 24.1_

- [ ] 3. MySQL Database Schema and Migrations
  - Create database and user accounts (with Secrets Manager integration)
  - Create User hierarchy tables: Master_User, Volunteer (with inheritance pattern)
  - Create OTP_Request table (phone_or_email, otp_code, expires_at, attempt_count, verified)
  - Create Session_Token table (user_id, token, created_at, expires_at, ip_address, user_agent, permissions_json)
  - Create Audit_Log table (immutable append-only: user_id, action, resource_type, resource_id, before_value, after_value, timestamp)
  - Create Guest table (guest_id, name, email, phone, company, profession, category, current_status, current_location, emergency_contact, special_requirements, event_id)
  - Create Event, EventSession, Location_Identifier, Check_In_Event, Check_Out_Event, Session_Attendance tables
  - Set up database indexes (guest_id, event_id, phone, email, timestamps)
  - Configure SERIALIZABLE isolation level for critical transactions
  - _Requirements: 24.1, 7.1, 9.7, 10.6_

  - [ ]* 3.1 Write property test for database persistence
    - **Property 13: Data Persistence Across Restarts**
    - **Validates: Requirement 24.1-24.3**

- [ ] 4. AWS CloudWatch Logging Setup
  - Create CloudWatch Log Groups: `/ecs/event-tracker-app`, `/audit/event-tracker`, `/alb/event-tracker-alb`, `/rds/event-tracker-db`
  - Set up log retention policies (30 days default)
  - Create CloudWatch Logs IAM role for ECS task execution
  - Create CloudWatch Alarms (RDS connection failures, ECS task failures, error rate spikes)
  - Set up CloudWatch Dashboards for monitoring (CPU, memory, error rate, request latency)
  - _Requirements: 25.1, 20.1_

- [ ] 5. ECR Container Registry Setup
  - Create AWS Elastic Container Registry (ECR) repository for Flask backend images
  - Set up repository lifecycle policies (keep last 10 images, remove old)
  - Configure ECR repository permissions (allow ECS task role to pull)
  - Set up image scanning on push (vulnerability detection)
  - Document ECR image tagging strategy (latest, git-commit-hash)
  - _Requirements: 25.1_

- [ ] 6. S3 and CloudFront Setup
  - Create S3 bucket for React.js SPA static assets
  - Configure S3 bucket policy for public read access (via CloudFront only)
  - Enable server-side encryption (AES-256)
  - Set up S3 bucket access logging
  - Create CloudFront distribution with S3 as origin
  - Configure CloudFront behaviors (index.html: no cache, static: 1-day cache)
  - Set up ACM certificate for CloudFront HTTPS
  - Configure origin access control (OAC) to restrict S3 access to CloudFront
  - _Requirements: 25.1, 25.3_

- [ ] 7. Application Load Balancer (ALB) Setup
  - Create CloudFormation template for ALB in public subnets (multi-AZ)
  - Configure target group pointing to ECS Fargate tasks on port 5000
  - Set up health check: POST /api/health (200 response, 30s interval)
  - Configure HTTPS listener (ACM certificate) on port 443
  - Set up HTTP to HTTPS redirect (port 80 → 443)
  - Configure security group (443 inbound, 5000 to ECS targets)
  - Enable ALB access logging to CloudWatch Logs
  - _Requirements: 25.1, 25.2_

- [ ] 8. ECS Fargate Cluster and Task Definition
  - Create CloudFormation template for ECS Fargate cluster
  - Create task definition for Flask backend (Python 3.11)
  - Configure CPU: 512 units, Memory: 1024 MB (adjustable per task)
  - Inject environment variables from AWS Secrets Manager (DB credentials, API keys)
  - Set up CloudWatch Logs configuration for task logging
  - Create ECS service with ALB target group integration
  - Configure auto-scaling policy (target: 70% CPU, min: 2 tasks, max: 20 tasks)
  - Set up IAM task execution role and task role with S3, Secrets Manager, CloudWatch permissions
  - _Requirements: 25.1, 25.2_

- [ ] 9. Infrastructure as Code (CloudFormation) Documentation
  - Document all CloudFormation stacks: VPC, RDS, ECS, ALB, S3, CloudFront, IAM
  - Create deployment guide with stack creation order and dependencies
  - Document parameter mappings (dev, staging, prod environments)
  - Create rollback procedures for failed deployments
  - Add monitoring and alerting setup instructions
  - _Requirements: 25.1_

- [ ] 10. Checkpoint - Infrastructure Complete
  - Verify VPC, subnets, security groups created successfully
  - Verify RDS instance is operational and accessible from ECS security group
  - Verify ECR repository created with lifecycle policies
  - Verify CloudFront distribution is operational
  - Verify ALB health check passes (create temporary backend response)
  - Verify CloudWatch Logs groups created and receiving logs
  - Ensure all infrastructure follows AWS best practices (multi-AZ, encryption, least privilege)

---

## Phase 2: Backend Foundation

### Objective

Establish Flask backend project structure, SQLAlchemy ORM, database connection pooling, CloudWatch logging, and core service infrastructure for Python-based backend.

---

- [ ] 11. Flask Project Setup
  - Create Python Flask project with blueprints for modular organization
  - Set up requirements.txt: Flask, Flask-SQLAlchemy, Flask-CORS, Boto3, Flask-Marshmallow, python-dotenv, requests, gunicorn, pymysql, python-json-logger
  - Create app factory pattern (create_app function) for multi-environment support
  - Configure Flask environment variables (FLASK_ENV: development, staging, production)
  - Set up Config classes (Config, DevelopmentConfig, ProductionConfig)
  - Create Dockerfile (Python 3.11-slim, gunicorn WSGI server)
  - Set up .dockerignore file
  - _Requirements: 25.1_

- [ ] 12. SQLAlchemy ORM and Database Connection
  - Install Flask-SQLAlchemy and PyMySQL driver
  - Configure SQLAlchemy engine with connection pooling (pool_size=20, max_overflow=40)
  - Implement pool_pre_ping for connection health verification
  - Set up connection pooling with recycle strategy (3600 seconds)
  - Create SQLAlchemy base model with common fields (id, created_at, updated_at, deleted_at)
  - Implement soft-delete pattern (deleted_at field, query filters exclude deleted)
  - Set up database session management and request lifecycle hooks
  - _Requirements: 24.1, 25.2_

- [ ] 13. CloudWatch Logging Integration
  - Integrate Python logging with AWS CloudWatch via Boto3
  - Configure JSON structured logging (python-json-logger) for analysis
  - Set up logging levels (INFO, WARNING, ERROR) with filters
  - Implement request/response logging middleware for all API endpoints
  - Log all user actions (auth, registration, check-in, queries) for audit trail
  - Create custom log formatters for consistent JSON structure
  - Add CloudWatch Logs client with error handling and fallback
  - _Requirements: 20.1, 25.1_

- [ ] 14. CORS Configuration and Security Middleware
  - Install and configure Flask-CORS for cross-origin requests from CloudFront
  - Set up CORS policy (CloudFront domain, /api/* routes only)
  - Implement custom security headers (CSP, X-Frame-Options, X-Content-Type-Options)
  - Add request ID generation for request tracing in logs
  - Implement error handling middleware (consistent JSON error responses)
  - Add rate limiting middleware for OTP endpoints (max 5 requests/hour per phone/email)
  - _Requirements: 25.1, 1.5_

- [ ] 15. Database Models - User Hierarchy
  - Create SQLAlchemy ORM models for Master_User and Volunteer classes
  - Implement inheritance hierarchy (Base User class, subclasses)
  - Add fields: id (UUID), email, phone, name, created_at, approval_status, last_login
  - Implement phone number normalization at model level
  - Create indexes on email, phone, approval_status
  - Implement model validation (required fields, format checks)
  - Add timestamps for audit trail (created_at, updated_at, deleted_at)
  - _Requirements: 1.1, 4.1, 5.1, 6.1_

- [ ] 16. Database Models - OTP and Session Management
  - Create OTP_Request ORM model (phone_or_email, otp_code, expires_at, attempt_count, verified)
  - Create Session_Token ORM model (user_id, token, created_at, expires_at, ip_address, user_agent, permissions_json)
  - Create Audit_Log ORM model (immutable append-only: user_id, action, resource_type, resource_id, before/after values)
  - Create indexes on otp_request (phone_or_email, expires_at), session_token (token, user_id), audit_log (user_id, timestamp)
  - Implement audit_log as immutable (inserts only, no updates; configure DB constraint)
  - _Requirements: 2.1, 2.4, 20.1, 20.3_

- [ ] 17. Database Models - Guest and Event Data
  - Create Guest ORM model (guest_id, name, email, phone, company, profession, category, current_status, current_location, emergency_contact, special_requirements, event_id)
  - Create GuestCategory enum (General_Attendee, VIP, Speaker, Staff, Volunteer, Press, Sponsor)
  - Create Event ORM model (event_id, name, description, start_date, end_date, capacity, created_by)
  - Create EventSession ORM model (session_id, event_id, name, scheduled_start, scheduled_end, location, description)
  - Create Location_Identifier ORM model (location_id, event_id, name, capacity, type)
  - Create indexes on guest (event_id, phone, current_status), event (created_at), session (event_id), location (event_id)
  - _Requirements: 7.1, 11.1, 11.6_

- [ ] 18. Database Models - Check-In/Check-Out and Attendance
  - Create Check_In_Event ORM model (checkin_id, guest_id, event_id, session_id, timestamp, location, volunteer_id, identification_method)
  - Create Check_Out_Event ORM model (checkout_id, guest_id, event_id, session_id, timestamp, location, volunteer_id, duration_minutes)
  - Create Session_Attendance ORM model (session_id, guest_id, event_id, check_in_time, check_out_time, duration_minutes)
  - Create indexes on check-in/check-out (guest_id, event_id, timestamp, location)
  - Create indexes on session_attendance (session_id, guest_id, event_id)
  - Implement efficient queries for current presence status (current_status = 'present')
  - _Requirements: 9.7, 10.6, 12.1, 12.5_

  - [ ]* 18.1 Write property test for database persistence
    - **Property 13: Data Persistence Across Restarts**
    - **Validates: Requirement 24.1-24.3**

- [ ] 19. Phone Number Validation Service
  - Implement PhoneValidator class with validation logic (+CC-XXXXXXXXXX format)
  - Implement country code extraction and digit validation (10 digits exactly)
  - Implement phone number normalization to standardized format
  - Add error messages for invalid formats (missing CC, wrong digit count)
  - Create utility function for phone normalization at application layer
  - Add validation to User model and guest registration endpoints
  - _Requirements: 3.1-3.6_

  - [ ]* 19.1 Write property test for phone normalization
    - **Property 2: Phone Number Normalization Idempotence**
    - **Validates: Requirements 3.1-3.5**

- [ ] 20. OTP Generation and Verification Service
  - Implement OTPService class with generateOTP() for email and SMS
  - Implement 6-digit random OTP generation with 5-minute TTL
  - Implement OTP verification with 3-retry limit and 15-minute lockout
  - Implement OTP request/verification state machine (pending → verified)
  - Add rate limiting: max 5 OTP requests per hour per phone/email
  - Implement delivery methods: sendOTPEmail() and sendOTPSMS() (external service integrations)
  - Add comprehensive error handling and logging
  - _Requirements: 1.5, 2.4-2.9, 4.4, 6.2_

  - [ ]* 20.1 Write property test for OTP validation round trip
    - **Property 1: OTP Validation Round Trip**
    - **Validates: Requirements 1.5-1.8, 2.4-2.7**

- [ ] 21. External Communication Services Integration
  - Implement Email_Service_Provider integration (SendGrid, AWS SES, or similar)
  - Implement SMS_Gateway integration (Twilio, AWS SNS, or similar)
  - Create EmailService class with sendOTPEmail() and sendNotificationEmail()
  - Create SMSService class with sendOTPSMS() and sendNotificationSMS()
  - Implement error handling and retry logic (exponential backoff)
  - Add logging for all delivery attempts (success, failure, retry)
  - Implement circuit breaker pattern for service resilience
  - _Requirements: 1.5-1.6, 3.6_

- [ ] 22. Session Management Service
  - Implement SessionManager class (createSession, validateSession, revokeSession)
  - Implement session token generation with secure random tokens (UUID or cryptographic)
  - Store session tokens in MySQL database with configurable TTL (8 hours)
  - Implement session validation with IP/user-agent binding for security
  - Add session expiration logic and cleanup job (periodic cleanup of expired sessions)
  - Implement session revocation on logout
  - Create session query methods (getSessionByToken, getActiveSessionsByUserId)
  - _Requirements: 2.1-2.9, 6.1-6.6_

- [ ] 23. Flask API Blueprint Structure
  - Create auth blueprint (POST /api/auth/otp-request, /otp-verify, /master-setup, /logout)
  - Create guests blueprint (POST /api/guests, /guests/batch, GET /api/guests, search)
  - Create checkin blueprint (POST /api/events/{event_id}/check-in, /check-out, status queries)
  - Create events blueprint (event/session/location management endpoints)
  - Create analytics blueprint (analytics, reporting, export endpoints)
  - Create queries blueprint (natural language query endpoints)
  - Create health blueprint (GET /api/health for ALB health check)
  - Register all blueprints with Flask app
  - _Requirements: 25.1_

- [ ] 24. Checkpoint - Backend Foundation Complete
  - Verify Flask app starts successfully and all blueprints are registered
  - Verify database connection pooling works (test 20+ concurrent connections)
  - Verify CloudWatch Logs receives application logs
  - Verify ORM models can perform CRUD operations
  - Verify phone validation and normalization work correctly
  - Verify OTP service generates and validates OTPs
  - Verify session management creates and validates tokens
  - Ensure all foundation tests pass

---

## Phase 3: Frontend Foundation

### Objective

Establish React.js single-page application structure, routing with React Router, state management with Context API, and deployment to S3/CloudFront.

---

- [ ] 25. React.js Project Setup and Structure
  - Create React.js project with Create React App or Vite
  - Install TypeScript support
  - Configure environment variables (.env.development, .env.production)
  - Set up folder structure (/src/components, /src/pages, /src/services, /src/hooks, /src/context, /src/utils)
  - Configure build output directory (/build)
  - Set up package.json scripts (start, build, test, deploy)
  - _Requirements: 25.1, 25.3_

- [ ] 26. React Router and Navigation
  - Install React Router v6
  - Create main routes (/, /login, /master-dashboard, /volunteer-dashboard, /setup, /guests, /analytics, /queries)
  - Implement route guards (authenticated, role-based access)
  - Create navigation component with conditional links based on role
  - Implement 404 and error pages
  - _Requirements: 25.3_

- [ ] 27. State Management with Context API
  - Create AuthContext for authentication state (user, session token, permissions)
  - Create EventContext for current event data (event_id, sessions, locations, guests)
  - Create DashboardContext for real-time metrics (attendance, capacity, updates)
  - Implement context providers and hooks (useAuth, useEvent, useDashboard)
  - Set up context persistence (localStorage for session token)
  - _Requirements: 25.3_

- [ ] 28. HTTP Client and API Service Layer
  - Create Axios configuration with base URL (ALB endpoint behind CloudFront)
  - Implement API service layer (/src/services/api.ts) with methods for all endpoints
  - Add request/response interceptors for authentication (session token in header)
  - Implement error handling (401 redirects to login, 403 shows access denied)
  - Add request timeout configuration (30 seconds)
  - _Requirements: 25.1, 25.3_

- [ ] 29. Authentication UI Components
  - Create LoginForm component (email/phone input, submit button)
  - Create OTPVerification component (OTP input field, timer for expiration)
  - Create MasterUserSetup component (email, phone, dual OTP verification)
  - Implement form validation (required fields, format checks)
  - Add error messages for invalid inputs or failed authentication
  - _Requirements: 2.1-2.10, 1.1-1.10_

- [ ] 30. React Build Configuration and Optimization
  - Configure Webpack for code splitting (lazy loading routes)
  - Set up environment-specific build variables (API base URL, CloudFront domain)
  - Configure source maps for development, minification for production
  - Set up CSS-in-JS or CSS modules for component styling
  - Configure asset optimization (image compression, tree shaking)
  - _Requirements: 25.3_

- [ ] 31. Build and Deployment to S3/CloudFront
  - Create build script (outputs to /build directory)
  - Create deployment script (AWS CLI: s3 sync, CloudFront invalidation)
  - Set up environment-specific deployment (dev, staging, prod)
  - Configure cache headers (versioned assets: max-age, HTML: no-cache)
  - Implement deployment verification (test deployed app via CloudFront)
  - _Requirements: 25.1, 25.3_

- [ ] 32. Responsive Design and Accessibility
  - Implement responsive layout (mobile-first, media queries)
  - Add accessibility features (ARIA labels, semantic HTML, keyboard navigation)
  - Test with screen readers (NVDA, JAWS)
  - Ensure color contrast meets WCAG AA standards
  - _Requirements: 25.3_

- [ ] 33. Checkpoint - Frontend Foundation Complete
  - Verify React app builds successfully (npm run build)
  - Verify all routes accessible and render correctly
  - Verify authentication components render and accept input
  - Verify API service layer can make requests
  - Verify build artifacts deployable to S3
  - Ensure app is responsive on mobile, tablet, desktop
  - Test accessibility with screen reader

---

## Phase 4: Authentication APIs

### Objective

Implement Flask REST endpoints for OTP-based authentication, Master user setup, volunteer management, and session management.

---

- [ ] 34. OTP Request Endpoint
  - Create POST /api/auth/otp-request endpoint
  - Accept JSON: {phone_or_email, purpose: "login"|"setup"|"verification"}
  - Validate phone format (+CC-XXXXXXXXXX)
  - Check rate limiting (max 5 OTP requests per hour per phone/email)
  - Call OTPService.generateOTP() to create OTP
  - Call EmailService or SMSService to deliver OTP
  - Log OTP request in audit trail
  - Return JSON: {success: true, message: "OTP sent", expires_in: 300}
  - _Requirements: 1.5, 2.4-2.7, 3.1_

- [ ] 35. OTP Verification Endpoint
  - Create POST /api/auth/otp-verify endpoint
  - Accept JSON: {phone_or_email, otp_code}
  - Validate OTP against stored OTP_Request record
  - Check expiration (5 minutes)
  - Check attempt count (max 3 failures, then 15-minute lockout)
  - Mark OTP as verified on success
  - Return JSON: {success: true, token: "session_token"} or error
  - _Requirements: 2.4-2.10, 6.2_

- [ ] 36. Master User Setup Endpoint
  - Create POST /api/auth/master-setup endpoint
  - Accept JSON: {email, phone, otp_email, otp_phone}
  - Check if any Master_User exists (first-time launch detection)
  - Verify both OTPs are valid
  - Create Master_User record with unique email and phone
  - Create session token with Master permissions
  - Log setup action in audit trail
  - Return JSON: {success: true, token: "session_token", user: master_user}
  - _Requirements: 1.1-1.10_

- [ ] 37. Master User Login Endpoint
  - Create POST /api/auth/login endpoint
  - Accept JSON: {phone_or_email}
  - Validate phone format if phone provided
  - Look up user (Master_User or Volunteer) by email or phone
  - Generate and deliver OTP
  - Log login attempt in audit trail
  - Return JSON: {success: true, message: "OTP sent", session_id: "temp_session"}
  - _Requirements: 2.1-2.10_

- [ ] 38. Session Validation Endpoint
  - Create GET /api/auth/validate endpoint
  - Accept Bearer token in Authorization header
  - Validate token against Session_Token table
  - Check expiration and IP/user-agent binding
  - Return JSON: {valid: true, user: user_data, permissions: [...]}
  - Return 401 Unauthorized if invalid or expired
  - _Requirements: 2.1-2.9, 6.1-6.6_

- [ ] 39. Logout Endpoint
  - Create POST /api/auth/logout endpoint
  - Accept Bearer token in Authorization header
  - Revoke session token (mark revoked or delete)
  - Log logout action in audit trail
  - Return JSON: {success: true, message: "Logged out"}
  - _Requirements: 2.1-2.9_

- [ ] 40. Volunteer Registration Endpoint
  - Create POST /api/volunteers/register endpoint
  - Accept JSON: {name, email, phone}
  - Validate phone format and normalize
  - Check if phone/email already exists
  - Create Volunteer account with status "pending_approval"
  - Generate and deliver OTP for phone verification
  - Log volunteer registration in audit trail
  - Return JSON: {success: true, message: "Registration pending approval"}
  - _Requirements: 4.1-4.8_

  - [ ]* 40.1 Write unit test for volunteer registration
    - Test valid registration with unique phone/email
    - Test duplicate phone/email error
    - Test phone validation error
    - _Requirements: 4.1-4.8_

- [ ] 41. Volunteer Approval Endpoint (Master User Only)
  - Create PUT /api/volunteers/{volunteer_id}/approve endpoint
  - Require Master_User session token
  - Update Volunteer status to "approved"
  - Generate and send approval SMS/email
  - Log approval action in audit trail (include approver ID)
  - Return JSON: {success: true, volunteer: updated_volunteer}
  - _Requirements: 5.1-5.8_

- [ ] 42. Volunteer Rejection Endpoint (Master User Only)
  - Create DELETE /api/volunteers/{volunteer_id}/reject endpoint
  - Require Master_User session token
  - Update Volunteer status to "rejected"
  - Send rejection notification to volunteer
  - Log rejection action in audit trail
  - Return JSON: {success: true, message: "Volunteer rejected"}
  - _Requirements: 5.1-5.8_

- [ ] 43. Pending Volunteers List Endpoint (Master User Only)
  - Create GET /api/volunteers?status=pending_approval endpoint
  - Require Master_User session token
  - Return list of volunteers with status "pending_approval"
  - Include: volunteer_id, name, email, phone, registration_timestamp
  - Return JSON: {success: true, volunteers: [...], total: N}
  - _Requirements: 5.1-5.8_

- [ ] 44. Checkpoint - Authentication APIs Complete
  - Verify OTP request endpoint generates OTP and delivers (mock SMS/Email)
  - Verify OTP verification endpoint validates correctly
  - Verify rate limiting blocks 6th OTP request within 1 hour
  - Verify Master user setup creates user and session token
  - Verify volunteer registration creates pending volunteer
  - Verify volunteer approval/rejection workflows
  - Test all auth endpoints with invalid inputs (expect error responses)
  - Verify audit trail logs all auth actions

---

## Phase 5: Guest Management

### Objective

Implement Flask endpoints for guest registration, batch registration, search, category management, and guest data validation.

---

- [ ] 45. Single Guest Registration Endpoint
  - Create POST /api/guests endpoint
  - Accept JSON: {name, email, phone, company, profession, category, emergency_contact, special_requirements, event_id}
  - Validate all required fields (name, phone, event_id)
  - Validate phone format and normalize
  - Check for duplicate guests (phone + event_id)
  - Create Guest record with generated UUID and registration timestamp
  - Log registration in audit trail (registrar_id from session)
  - Return JSON: {success: true, guest: guest_data}
  - _Requirements: 7.1-7.9_

- [ ] 46. Guest Retrieval Endpoints
  - Create GET /api/guests/{guest_id} endpoint (retrieve single guest)
  - Create GET /api/guests endpoint with optional filters (event_id, category, name)
  - Implement pagination support (limit, offset)
  - Return guest data including current_status and current_location
  - _Requirements: 7.1-7.9, 13.2_

- [ ] 47. Guest Search Endpoint
  - Create GET /api/guests/search endpoint
  - Accept query parameters: {name?, email?, phone?, badge_number?, ticket_number?, event_id}
  - Implement name search (substring matching, case-insensitive)
  - Implement phone search (exact match)
  - Implement email search (exact match)
  - Return matching guests with pagination
  - _Requirements: 8.1-8.5_

- [ ] 48. Batch Guest Registration Endpoint
  - Create POST /api/guests/batch endpoint
  - Accept JSON: {guests: [{name, email, phone, ...}, ...], event_id}
  - Enforce 100-guest maximum per batch
  - Validate all guests before atomic batch insert
  - Implement transaction with all-or-nothing semantics
  - Log batch registration in audit trail (registrar_id, batch_id)
  - Return JSON: {success: true, created: N, failed: M, results: [{guest_id, status}, ...]}
  - _Requirements: 7.10_

  - [ ]* 48.1 Write property test for batch registration atomicity
    - **Property 14: Batch Registration Atomicity**
    - **Validates: Requirement 7.10**

- [ ] 49. Guest Update Endpoint
  - Create PUT /api/guests/{guest_id} endpoint
  - Accept JSON with updatable fields (name, email, company, profession, emergency_contact)
  - Validate phone immutability (cannot change phone number)
  - Update guest record and record change in audit trail (before/after values)
  - Return JSON: {success: true, guest: updated_guest}
  - _Requirements: 7.1-7.9_

- [ ] 50. Guest Delete Endpoint (Master User Only)
  - Create DELETE /api/guests/{guest_id} endpoint
  - Require Master_User session token
  - Soft delete guest (set deleted_at timestamp)
  - Log deletion in audit trail
  - Return JSON: {success: true, message: "Guest deleted"}
  - _Requirements: 7.1-7.9_

- [ ] 51. Guest Category Validation
  - Implement GuestCategory enum validation (7 categories)
  - Add category validation to registration and update endpoints
  - Create category-based filtering in search/list endpoints
  - _Requirements: 8.1-8.5_

- [ ] 52. Guest Data Model Validation
  - Implement validation service for guest data (required fields, format)
  - Validate email format (RFC 5322 simplified)
  - Validate phone format (+CC-XXXXXXXXXX)
  - Validate required fields: name, phone, event_id
  - Return detailed validation errors for each field
  - _Requirements: 7.1-7.9_

  - [ ]* 52.1 Write property test for guest data persistence
    - **Property 4: Guest Registration Persistence**
    - **Validates: Requirement 7.1-7.9**

- [ ] 53. Checkpoint - Guest Management Complete
  - Test single guest registration with valid data
  - Test guest registration with invalid phone format (expect error)
  - Test batch registration with 50 guests (expect atomic creation)
  - Test batch registration with 101 guests (expect error: max 100)
  - Test guest search by name, phone, email
  - Test guest update (name, company, etc.)
  - Test guest delete (soft delete)
  - Verify all guest operations logged in audit trail

---

## Phase 6: Check-In/Check-Out Engine

### Objective

Implement Flask REST endpoints for check-in/check-out transaction processing with concurrency safety, guest identification, and real-time status updates.

---

- [ ] 54. Check-In Endpoint (Core Logic)
  - Create POST /api/events/{event_id}/check-in endpoint
  - Require Volunteer or Master_User session token
  - Accept JSON: {guest_id, session_id?, location_id, identification_method}
  - Validate guest exists and belongs to event
  - Validate location_id exists in event
  - Look up guest by identification method (name search, badge, ticket)
  - Acquire pessimistic lock on guest record (30-second timeout)
  - Check if guest already checked in (current_status == "present")
  - Create Check_In_Event record: guest_id, event_id, session_id, timestamp, location_id, volunteer_id
  - Update Guest record: current_status = "present", current_location = location_id
  - Create or update Session_Attendance if session_id provided
  - Log check-in in audit trail
  - Release lock
  - Return JSON: {success: true, guest: guest_data, timestamp, location}
  - Target persistence: < 500ms SLA
  - _Requirements: 9.1-9.11, 22.1_

  - [ ]* 54.1 Write property test for check-in concurrency safety
    - **Property 5: Check-In Creates Concurrent-Safe Records**
    - **Validates: Requirements 9.7, 21.1, 21.3**

- [ ] 55. Check-Out Endpoint (Core Logic)
  - Create POST /api/events/{event_id}/check-out endpoint
  - Require Volunteer or Master_User session token
  - Accept JSON: {guest_id, session_id?, location_id}
  - Validate guest exists and is checked in (current_status == "present")
  - Validate location_id exists in event
  - Acquire pessimistic lock on guest record (30-second timeout)
  - Look up most recent Check_In_Event for guest
  - Calculate duration: (now - check_in_time) in minutes
  - Create Check_Out_Event: guest_id, event_id, session_id, timestamp, location_id, volunteer_id, duration_minutes
  - Update Guest record: current_status = "departed", current_location = NULL
  - Update Session_Attendance if session_id provided: check_out_time, duration_minutes
  - Log check-out in audit trail
  - Release lock
  - Return JSON: {success: true, guest: guest_data, duration_minutes, check_out_time}
  - Target persistence: < 500ms SLA
  - _Requirements: 10.1-10.11, 22.2_

  - [ ]* 55.1 Write property test for check-out requirements
    - **Property 6: Check-Out Requires Active Check-In**
    - **Validates: Requirements 10.10-10.11, 22.3-22.4**

  - [ ]* 55.2 Write property test for duration calculation
    - **Property 7: Duration Calculation Accuracy**
    - **Validates: Requirements 10.8, 12.4**

- [ ] 56. Duplicate Check-In Detection and Re-Check-In
  - Implement check-in detection: if current_status == "present", return warning
  - Allow re-check-in with confirmation (include warning in response)
  - Track re-check-in events in audit trail for analysis
  - Display warning to volunteer: "Guest already checked in at HH:MM at Location. Check in again?"
  - _Requirements: 9.11, 22.1_

- [ ] 57. Guest Current Status and Location Queries
  - Create GET /api/guests/{guest_id}/status endpoint
  - Return current guest status: {guest_id, current_status, current_location, last_check_in_time}
  - Create GET /api/events/{event_id}/guests?current_status=present endpoint
  - Return list of guests currently present with locations
  - Create GET /api/events/{event_id}/guests?current_status=departed endpoint
  - Return list of guests who have checked out
  - _Requirements: 9.8, 10.7, 13.2_

- [ ] 58. Session-Specific Check-In/Check-Out
  - Modify check-in endpoint to support session_id parameter
  - On first check-in to session: create Session_Attendance record (lazy initialization)
  - Track session-specific attendance separately from event-level
  - On check-out from session: update Session_Attendance with check_out_time
  - Calculate session-specific duration
  - Support guest checking into multiple sessions within same event
  - _Requirements: 12.1-12.5_

- [ ] 59. Volunteer Enforcement
  - Add check to both endpoints: require Volunteer or Master_User role
  - Reject requests from Guest-level users (401 Unauthorized)
  - Record volunteer_id in all Check_In_Event and Check_Out_Event records
  - Display volunteer identification in response confirmations
  - _Requirements: 9.10, 10.10_

- [ ] 60. Check-In/Check-Out Confirmation Response Format
  - Include guest name, category, timestamp in check-in response
  - Highlight VIP/Speaker category in response (flag: is_vip_or_speaker)
  - Include special requirements (dietary, accessibility) if present
  - Include duration and departure time in check-out response
  - Include volunteer name/ID in both responses
  - _Requirements: 9.9, 10.9, 8.4_

- [ ] 61. Concurrency Testing and Stress Testing
  - Create stress test endpoint with concurrent_count parameter
  - Simulate N concurrent check-in requests (test with 50, 100, 200)
  - Verify exactly N Check_In_Event records created (no duplicates)
  - Verify no database consistency violations
  - Verify final guest state is consistent
  - Measure actual persistence latency (should be < 500ms)
  - _Requirements: 21.1-21.5_

  - [ ]* 61.1 Write integration test for concurrency handling
    - Test 50+ simultaneous check-ins
    - Verify database consistency
    - Verify no race conditions

- [ ] 62. Checkpoint - Check-In/Check-Out Engine Complete
  - Verify Properties 5, 6, 7 pass with 100+ iterations
  - Run stress test with 100+ concurrent operations (verify SLA)
  - Manually test check-in/check-out with real guest data
  - Verify audit trail logs all check-in/check-out events
  - Test duplicate check-in detection and re-check-in workflow
  - Test session-specific check-in/check-out workflows
  - Verify lock timeout handling (no deadlocks)

---

## Phase 7: Real-Time Dashboard

### Objective

Implement Flask REST endpoints for real-time attendance metrics aggregation, capacity monitoring, and dashboard data queries (using direct RDS queries, no caching layer).

---

- [ ] 63. Real-Time Attendance Metrics Aggregation
  - Implement GET /api/events/{event_id}/dashboard endpoint
  - Query current guest count with status = 'present'
  - Query total registered guests count
  - Query guests with status = 'not_checked_in'
  - Query guests with status = 'departed'
  - Calculate peak attendance from historical Check_In events
  - Add timestamp for data freshness (last_updated)
  - Return JSON: {current_present: N, total_registered: M, not_checked_in: X, departed: Y, peak_attendance: Z, last_updated: timestamp}
  - _Requirements: 13.1-13.5_

- [ ] 64. Attendance Breakdown by Category
  - Implement GET /api/events/{event_id}/analytics/by-category endpoint
  - Group current attendance by Guest_Category (7 categories)
  - Return map of category → {count: N, percentage: X%}
  - Update in real-time as check-ins/check-outs occur
  - _Requirements: 13.5, 8.5_

- [ ] 65. Attendance Breakdown by Location
  - Implement GET /api/events/{event_id}/analytics/by-location endpoint
  - Track current guest count at each Location_Identifier
  - Update current_location field in Guest table on check-in
  - Return map of location → {count: N, capacity: C, percentage: X%}
  - Support location-based capacity monitoring
  - _Requirements: 13.8, 23.2-23.3_

- [ ] 66. Real-Time Dashboard Query Endpoint
  - Implement GET /api/events/{event_id}/attendance endpoint
  - Return detailed attendance data with guest list
  - Include guest names, categories, current locations, check-in times
  - Filter by current_status, category, location as optional parameters
  - Implement pagination (limit, offset)
  - Ensure response time < 500ms (direct RDS queries, no caching)
  - _Requirements: 13.1-13.8_

- [ ] 67. Capacity Monitoring and Alerts
  - Implement GET /api/events/{event_id}/capacity endpoint
  - Calculate percentage of capacity used (current_attendance / capacity)
  - Return status: 'normal' (<80%), 'warning' (80-99%), 'critical' (≥100%)
  - Display warning indicator at 80% of capacity
  - Display alert at 100% of capacity
  - Track capacity at event level and location level
  - Return JSON: {capacity: C, current_count: N, percentage: X%, status: "normal"|"warning"|"critical"}
  - _Requirements: 23.1-23.5_

  - [ ]* 67.1 Write property test for capacity monitoring
    - **Property 15: Capacity Monitoring Consistency**
    - **Validates: Requirements 23.2-23.3**

- [ ] 68. Capacity Override for Master User
  - Implement POST /api/events/{event_id}/capacity-override endpoint
  - Require Master_User session token
  - Allow check-in to exceed capacity with override + note
  - Record override action in audit log
  - Display override warning in check-in confirmation
  - Log override events for later review
  - _Requirements: 23.4_

- [ ] 69. React Dashboard Components
  - Create DashboardPage component displaying current metrics
  - Display: total registered, currently present, checked out, not checked in
  - Create AttendanceByCategory component (visualization)
  - Create AttendanceByLocation component (visualization)
  - Display last updated timestamp
  - Implement polling mechanism for real-time updates (5-10 second intervals)
  - _Requirements: 13.1-13.8_

- [ ] 70. Checkpoint - Real-Time Dashboard Complete
  - Verify dashboard queries return < 500ms response time
  - Test capacity monitoring accuracy with sample data
  - Verify capacity alerts trigger at correct thresholds
  - Test dashboard components with live data
  - Verify attendance breakdowns by category and location are correct
  - Test polling mechanism updates dashboard every 5-10 seconds

---

## Phase 8: Analytics & Reporting

### Objective

Implement Flask endpoints for comprehensive attendance analytics, reporting, and data export in multiple formats (CSV, JSON, Excel, PDF).

---

- [ ] 71. Attendance Analytics and Report Generation
  - Implement GET /api/events/{event_id}/analytics endpoint
  - Aggregate metrics: total_registered, total_checked_in, total_checked_out, peak_attendance
  - Include timestamp (when report was generated)
  - Support optional time range filtering (start_date, end_date)
  - Return JSON with all metrics
  - _Requirements: 14.1-14.7_

- [ ] 72. Hourly Attendance Breakdown
  - Implement GET /api/events/{event_id}/analytics/hourly endpoint
  - Group Check_In events by hour of day
  - Return map of hour → {check_in_count, check_out_count, current_attendance}
  - Support time range filtering
  - Return JSON: {hourly_breakdown: [{hour: H, checkins: N, checkouts: M, current: X}, ...]}
  - _Requirements: 14.3_

- [ ] 73. Session-Specific Analytics
  - Implement GET /api/events/{event_id}/analytics/sessions endpoint
  - For each Event_Session: calculate total attendees, average duration, check-in/check-out counts
  - Include session metadata (name, scheduled time, actual participation)
  - Sort by attendance or duration
  - Return JSON: {sessions: [{session_id, name, total_attendees, avg_duration, checkins, checkouts}, ...]}
  - _Requirements: 14.5, 12.1-12.5_

- [ ] 74. Category-Based Analytics
  - Implement GET /api/events/{event_id}/analytics/categories endpoint
  - For each Guest_Category: count of attendees, check-in rate, check-out rate, avg duration
  - Return category breakdown with statistics
  - Support time range filtering
  - Return JSON: {categories: [{category, count, checkin_rate, checkout_rate, avg_duration}, ...]}
  - _Requirements: 14.4, 8.5_

- [ ] 75. Peak Attendance Time Detection
  - Implement GET /api/events/{event_id}/analytics/peak-time endpoint
  - Scan all Check_In events to find timestamp with maximum current attendance
  - Return timestamp and peak count
  - Support time range filtering
  - Return JSON: {peak_time: timestamp, peak_count: N}
  - _Requirements: 14.2_

- [ ] 76. Data Export to CSV Format
  - Implement GET /api/events/{event_id}/export?format=csv endpoint
  - Export guest data with proper comma separation
  - Export check-in/check-out events with timestamps
  - Export session attendance records
  - Quote fields containing special characters
  - Return CSV string or file stream with Content-Type: text/csv
  - _Requirements: 15.3_

- [ ] 77. Data Export to JSON Format
  - Implement JSON export endpoint
  - Export data with proper JSON structure (valid JSON)
  - Support nested objects for related data
  - Include metadata (export timestamp, event info)
  - Return JSON file with Content-Type: application/json
  - _Requirements: 15.4_

- [ ] 78. Data Export to Excel Format
  - Implement Excel export endpoint (requires openpyxl library)
  - Create workbook with multiple worksheets (guests, sessions, check-in/check-out, summary)
  - Format headers and apply styles
  - Include summary statistics sheet
  - Return Excel file (Buffer) with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - _Requirements: 15.5_

- [ ] 79. Data Export to PDF Format
  - Implement PDF export endpoint (requires reportlab or similar)
  - Generate PDF with formatted report (title, summary, tables, charts)
  - Include chart visualization (attendance over time, category breakdown)
  - Format tables with headers and alternating row colors
  - Return PDF file (Buffer) with Content-Type: application/pdf
  - _Requirements: 15.6_

- [ ] 80. Export Button and Endpoint
  - Create unified export endpoint: GET /api/events/{event_id}/analytics/export?format=csv|json|excel|pdf
  - Implement format selection
  - Return file with appropriate content-type header
  - Implement download link for user download
  - Log export requests in audit trail
  - _Requirements: 15.1-15.7_

- [ ] 81. React Reports Component
  - Create ReportsPage component accessible to Master_User and Volunteer
  - Display report type options (attendance, by category, by session, hourly)
  - Implement time range picker (date filters)
  - Display generated report with tables/charts
  - Implement export button for each format
  - _Requirements: 14.1_

- [ ] 82. Checkpoint - Analytics & Reporting Complete
  - Generate sample reports with test data
  - Verify all export formats produce valid files
  - Test PDF generation with charts and tables
  - Verify Excel workbook has all sheets and formatting
  - Manually review CSV and JSON exports for correctness

---

## Phase 9: Natural Language Query Interface

### Objective

Implement LLM-based natural language query processing with role-based access control, data anonymization, query execution, and caching (using direct RDS queries without Redis).

---

- [ ] 83. Query Interpretation via LLM
  - Implement NLQueryProcessor class with interpretQuery() method
  - Send user's plain English query to LLM (OpenAI GPT-4 or similar)
  - Parse LLM response to extract: intent, entities, filters, aggregation
  - Map intent to supported query types (COUNT_CURRENT_ATTENDEES, SEARCH_BY_PROFESSION, etc.)
  - Handle LLM timeout (30 seconds max)
  - _Requirements: 16.2, 17.1-17.7_

- [ ] 84. Supported Query Types Implementation
  - Implement COUNT_CURRENT_ATTENDEES query
  - Implement SEARCH_BY_PROFESSION query
  - Implement SEARCH_BY_NAME query
  - Implement FILTER_BY_CATEGORY_AND_STATUS query
  - Implement SEARCH_BY_COMPANY query
  - Implement COUNT_WITH_CRITERIA query
  - Implement ATTENDANCE_TRENDS query
  - _Requirements: 17.1-17.7_

- [ ] 85. Role-Based Access Control in Queries
  - Implement query access control enforcement
  - Master_User: access to all event data
  - Volunteer: restrict results to authorized events only
  - Filter query results based on authenticated user's permissions
  - Return empty results or access-denied if unauthorized
  - Log all query access attempts (authorized and unauthorized)
  - _Requirements: 18.1-18.5_

  - [ ]* 85.1 Write property test for query access control
    - **Property 10: Natural Language Query Access Control**
    - **Validates: Requirements 18.2-18.4**

- [ ] 86. Data Anonymization for LLM
  - Implement data anonymization layer before sending to LLM
  - Strip personal identifiers (names, emails, phone numbers) from queries
  - Send only aggregated/anonymized data (counts, categories, locations)
  - Never send guest details to external LLM service
  - _Requirements: 16.3_

- [ ] 87. Query Execution and Result Aggregation
  - Implement executeInterpreted() method
  - Execute interpreted query against database with parameterized queries
  - Aggregate results (counts, groupings, filters)
  - Apply anonymization before returning results
  - Include execution time metadata
  - _Requirements: 16.4_

- [ ] 88. Query Response Generation by LLM
  - Implement generateResponse() method
  - Send query result + interpretation to LLM for human-readable response
  - LLM formats response as natural language
  - Handle LLM timeout
  - Ensure response includes key metrics
  - _Requirements: 16.5-16.6_

- [ ] 89. Query Caching Infrastructure (RDS-Based)
  - Implement QueryCache interface (getCached, setCached, invalidateForEvent)
  - Generate query hash from normalized query string
  - Store cached results in database table (query_cache) with 5-minute TTL
  - Verify cache entries before returning (not older than 5 minutes)
  - _Requirements: 19.1-19.2, 19.4_

- [ ] 90. Query Cache Invalidation
  - Implement cache invalidation on Check_In/Check_Out events
  - Invalidate all cached queries for affected event
  - Invalidate queries for affected guest (optional)
  - Maintain cache coherency (new data available within 5 minutes)
  - _Requirements: 19.4-19.5_

  - [ ]* 90.1 Write property test for query cache invalidation
    - **Property 11: Query Cache Invalidation**
    - **Validates: Requirements 19.3-19.5**

- [ ] 91. Query Logging and Audit Trail
  - Implement query logging for all natural language queries
  - Log: user_id, original query text, query hash, timestamp, response, data accessed
  - Include cache hit status in log
  - Make logs queryable by user and date
  - Ensure audit trail immutable
  - _Requirements: 16.7, 18.5_

- [ ] 92. React Natural Language Query Component
  - Create QueryPage component with text input field
  - Display input placeholder suggesting example queries
  - Submit query and display LLM-generated response
  - Show query execution time and cache status
  - Implement query history (recent queries)
  - Accessible to Master_User and approved Volunteer only
  - _Requirements: 16.1_

- [ ] 93. Checkpoint - Natural Language Queries Complete
  - Verify Property 10 (access control enforcement)
  - Verify Property 11 (cache invalidation)
  - Test 10+ sample queries of all supported types
  - Verify cache hits reduce response time by 5x
  - Verify anonymization (no PII in LLM requests)
  - Verify audit trail logs all queries

---

## Phase 10: Frontend Components

### Objective

Implement React components for all features: authentication, guest management, check-in/check-out, dashboard, analytics, and natural language queries.

---

- [ ] 94. Guest Management Components
  - Create GuestRegistrationForm component (single guest registration)
  - Create BatchGuestUpload component (CSV file upload for batch registration)
  - Create GuestSearchComponent (search by name, email, phone)
  - Create GuestListComponent (display guests with pagination)
  - Create GuestDetailComponent (view/edit single guest)
  - _Requirements: 7.1-7.10, 8.1-8.5_

- [ ] 95. Check-In/Check-Out Components
  - Create CheckInForm component (guest selection, location, identification method)
  - Create CheckOutForm component (guest selection, location)
  - Create CheckInConfirmation component (display check-in details)
  - Create CheckOutConfirmation component (display check-out details with duration)
  - Display special requirements and VIP status prominently
  - _Requirements: 9.1-9.11, 10.1-10.11_

- [ ] 96. Volunteer Management Components
  - Create VolunteerRegistrationForm component
  - Create PendingVolunteersComponent (Master_User approval UI)
  - Create VolunteerApprovalForm component (approve/reject with notes)
  - Display volunteer status and approval timestamp
  - _Requirements: 4.1-4.8, 5.1-5.8_

- [ ] 97. Event and Session Management Components
  - Create EventForm component (create/edit event)
  - Create SessionForm component (create/edit session)
  - Create LocationForm component (create/edit location)
  - Create EventListComponent (list events with filters)
  - _Requirements: 11.1-11.6_

- [ ] 98. Analytics and Reporting Components
  - Create AnalyticsPage component (generate reports)
  - Create CategoryBreakdownChart component (visualization)
  - Create LocationBreakdownChart component (visualization)
  - Create HourlyAttendanceChart component (visualization)
  - Create ExportButtonComponent (CSV, JSON, Excel, PDF)
  - _Requirements: 14.1-14.7, 15.1-15.7_

- [ ] 99. Utility and Layout Components
  - Create Layout component (header, navigation, footer)
  - Create ErrorBoundary component (error handling)
  - Create LoadingSpinner component
  - Create FormInput component (reusable form field)
  - Create Modal component (reusable modal dialog)
  - Create Table component (reusable data table with sorting/pagination)
  - _Requirements: 25.3_

- [ ] 100. Checkpoint - Frontend Components Complete
  - Verify all components render correctly
  - Test form validation and error messages
  - Test data display with sample data
  - Test responsive layout on mobile/tablet/desktop
  - Verify accessibility of all components

---

## Phase 11: Testing & Deployment

### Objective

Implement comprehensive test suites, performance optimization, CI/CD pipeline, and deployment automation.

---

- [ ] 101. Unit Test Suite - Authentication Module
  - Test OTP generation with valid phone/email
  - Test OTP verification with correct code
  - Test OTP verification with incorrect code (3 failures)
  - Test OTP expiration after 5 minutes
  - Test 15-minute lockout after 3 failures
  - Test phone number normalization
  - Test session token creation and validation
  - Test session token expiration
  - Target: 95%+ code coverage for auth module
  - _Requirements: 1.0, 2.0, 3.0, 6.0_

- [ ] 102. Unit Test Suite - Guest Management Module
  - Test single guest registration with all fields
  - Test guest validation (required fields, formats)
  - Test batch guest registration (100 guests)
  - Test guest search by name, ticket, badge, category
  - Test guest data updates
  - Test category validation
  - Target: 95%+ code coverage for guest module
  - _Requirements: 7.0, 8.0, 14.0, 15.0_

- [ ] 103. Unit Test Suite - Check-In/Check-Out Module
  - Test check-in with guest retrieval
  - Test check-out with active check-in
  - Test check-out without active check-in (failure)
  - Test duration calculation
  - Test duplicate check-in detection
  - Test location validation
  - Test concurrent lock acquisition
  - Target: 95%+ code coverage for check-in/out module
  - _Requirements: 9.0, 10.0, 22.0_

- [ ] 104. Unit Test Suite - Analytics Module
  - Test attendance aggregation
  - Test hourly breakdown calculation
  - Test category breakdown
  - Test session attendance statistics
  - Test peak attendance detection
  - Test export format generation (CSV, JSON, Excel, PDF)
  - Target: 95%+ code coverage for analytics module
  - _Requirements: 14.0, 15.0_

- [ ] 105. Integration Test Suite - Full Workflows
  - Test complete Master_User setup → login → guest registration → check-in → check-out flow
  - Test Volunteer registration → approval → login → check-in flow
  - Test batch registration → report generation flow
  - Test natural language query flow with caching
  - Test concurrent check-in/check-out with 50+ simultaneous operations
  - Test data persistence across system restart
  - Target: All critical workflows tested
  - _Requirements: All requirements_

- [ ] 106. Property-Based Test Execution and Verification
  - Execute Property 1 tests (OTP round trip) - 100+ iterations
  - Execute Property 2 tests (phone normalization) - 100+ iterations
  - Execute Property 4 tests (guest persistence) - 100+ iterations
  - Execute Property 5 tests (check-in concurrency) - 20+ iterations with 50+ concurrent ops
  - Execute Property 6 tests (check-out requirements) - 100+ iterations
  - Execute Property 7 tests (duration accuracy) - 1000+ iterations
  - Execute Property 10 tests (query access control) - 100+ queries
  - Execute Property 11 tests (cache invalidation) - 100+ cache operations
  - Execute Property 13 tests (data persistence) - 10+ restarts
  - Execute Property 14 tests (batch atomicity) - 50+ batches
  - Execute Property 15 tests (capacity consistency) - 500+ capacity state changes
  - Verify all properties pass successfully

- [ ] 107. Performance Testing and Optimization
  - Test 100,000+ concurrent guest registrations (batch mode)
  - Test 500 simultaneous check-in/check-out operations
  - Measure dashboard latency (target: <2 seconds initial, <5 seconds updates)
  - Measure query execution time (target: <500ms with cache)
  - Measure audit log query performance (1M+ records)
  - Identify and optimize slow queries (database indexes)
  - Profile application memory usage
  - Load test with production-like data volume
  - Document performance benchmarks
  - _Requirements: All performance targets_

- [ ] 108. Security Testing and Hardening
  - Test OTP brute force (verify 15-minute lockout)
  - Test session token expiration and revocation
  - Test role-based access control enforcement
  - Test PII handling (verify no personal identifiers sent to LLM)
  - Test SQL injection prevention
  - Test rate limiting
  - Test unauthorized access attempts
  - Test data encryption at rest and in transit
  - Perform security audit of all endpoints
  - Document security findings and mitigations
  - _Requirements: All security requirements_

- [ ] 109. CI/CD Pipeline Setup
  - Set up GitHub Actions (or AWS CodePipeline) workflow
  - Configure build job: install dependencies, run tests, build Flask app, build React app
  - Configure unit/integration test job with coverage reporting
  - Configure Docker image build and push to ECR
  - Configure CloudFormation deployment with CloudFormation templates
  - Set up approval gate for production deployment
  - Configure automatic deployment to dev/staging on commit to main
  - _Requirements: 25.1_

- [ ] 110. Documentation and Deployment Preparation
  - Write API documentation (OpenAPI/Swagger)
  - Write database schema documentation
  - Write deployment guide (local, Docker, AWS)
  - Write configuration guide (environment variables, settings)
  - Write troubleshooting guide (common issues)
  - Write security guide (best practices, configuration)
  - Create Docker containerization (Dockerfile, Makefile)
  - Set up monitoring and alerting (CloudWatch Logs, Alarms)
  - Create backup and recovery procedures
  - _Requirements: All requirements_

- [ ] 111. Final Checkpoint - System Complete and Ready
  - All 15 properties passing with 100% success rate
  - All unit tests passing (95%+ coverage)
  - All integration tests passing
  - Performance benchmarks met (< 2s dashboard, < 500ms queries, 1000+ concurrent)
  - Security tests passed (no vulnerabilities found)
  - Documentation complete
  - Docker images built and tested
  - CI/CD pipeline functional
  - System ready for production deployment

---

## Notes

### Optional Test Tasks

Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP delivery. However, they validate critical correctness properties and are strongly recommended:

- **3.1**: Property 13 - Database persistence
- **18.1**: Property 13 - Database persistence (phase 2)
- **19.1**: Property 2 - Phone normalization
- **20.1**: Property 1 - OTP round trip
- **40.1**: Volunteer registration unit tests
- **48.1**: Property 14 - Batch registration atomicity
- **52.1**: Property 4 - Guest data persistence
- **54.1**: Property 5 - Check-in concurrency safety
- **55.1**: Property 6 - Check-out requirements
- **55.2**: Property 7 - Duration calculation accuracy
- **61.1**: Integration test for concurrency handling
- **67.1**: Property 15 - Capacity monitoring consistency
- **85.1**: Property 10 - Query access control
- **90.1**: Property 11 - Cache invalidation

### Implementation Strategy

1. **Sequential Phases**: Phases build on each other. Phase 1 must complete before Phase 2.
2. **Early Property Testing**: Core properties are tested as soon as implementation completes
3. **Checkpoint Tasks**: Each phase ends with a checkpoint to verify functionality
4. **Cloud-Native**: All infrastructure uses AWS managed services (no Redis, direct RDS queries)
5. **Technology Stack**: Python Flask, React.js, MySQL RDS, CloudWatch Logs, ECS Fargate, S3/CloudFront, ALB
6. **Scalability**: Each phase considers concurrent operations and performance targets

### Requirements Traceability

Every task is traced to specific requirements using `_Requirements: X.Y_` annotations. Use these to navigate from implementation tasks back to business requirements. Properties bridge formal correctness to business requirements.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1", "4.1", "5.1", "6.1", "7.1", "8.1"] },
    { "id": 1, "tasks": ["9.1", "10.1"] },
    { "id": 2, "tasks": ["11.1", "12.1", "13.1", "14.1"] },
    { "id": 3, "tasks": ["15.1", "16.1", "17.1", "18.1", "19.1", "20.1"] },
    { "id": 4, "tasks": ["21.1", "22.1", "23.1", "24.1"] },
    { "id": 5, "tasks": ["25.1", "26.1", "27.1", "28.1"] },
    { "id": 6, "tasks": ["29.1", "30.1", "31.1", "32.1"] },
    { "id": 7, "tasks": ["33.1"] },
    { "id": 8, "tasks": ["34.1", "35.1", "36.1", "37.1", "38.1", "39.1"] },
    { "id": 9, "tasks": ["40.1", "41.1", "42.1", "43.1"] },
    { "id": 10, "tasks": ["44.1"] },
    { "id": 11, "tasks": ["45.1", "46.1", "47.1", "48.1", "49.1", "50.1"] },
    { "id": 12, "tasks": ["51.1", "52.1", "53.1"] },
    { "id": 13, "tasks": ["54.1", "55.1", "56.1", "57.1", "58.1"] },
    { "id": 14, "tasks": ["59.1", "60.1", "61.1", "62.1"] },
    { "id": 15, "tasks": ["63.1", "64.1", "65.1", "66.1", "67.1"] },
    { "id": 16, "tasks": ["68.1", "69.1", "70.1"] },
    { "id": 17, "tasks": ["71.1", "72.1", "73.1", "74.1", "75.1"] },
    { "id": 18, "tasks": ["76.1", "77.1", "78.1", "79.1", "80.1"] },
    { "id": 19, "tasks": ["81.1", "82.1"] },
    { "id": 20, "tasks": ["83.1", "84.1", "85.1", "86.1"] },
    { "id": 21, "tasks": ["87.1", "88.1", "89.1", "90.1"] },
    { "id": 22, "tasks": ["91.1", "92.1", "93.1"] },
    { "id": 23, "tasks": ["94.1", "95.1", "96.1", "97.1"] },
    { "id": 24, "tasks": ["98.1", "99.1", "100.1"] },
    { "id": 25, "tasks": ["101.1", "102.1", "103.1", "104.1"] },
    { "id": 26, "tasks": ["105.1", "106.1", "107.1"] },
    { "id": 27, "tasks": ["108.1", "109.1", "110.1"] },
    { "id": 28, "tasks": ["111.1"] }
  ]
}
```
