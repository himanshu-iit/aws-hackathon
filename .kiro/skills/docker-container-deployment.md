# Docker & Container Deployment

## Overview
Container orchestration and deployment using Docker, Dockerfile best practices, ECR registry, and ECS Fargate container management.

## Key Skills

### Docker Fundamentals
- Dockerfile syntax and best practices
- Multi-stage builds for optimization
- Layer caching and build optimization
- Base image selection (python:3.11-slim)
- Entrypoint and CMD directives
- Container networking and ports
- Volume mounting for data persistence

### Docker Image Management
- Image building and tagging
- Image optimization (minimal size, security)
- Vulnerability scanning
- Image versioning strategies
- Docker Compose for local development

### AWS ECR (Elastic Container Registry)
- Repository creation and management
- Image push/pull operations
- Lifecycle policies for image cleanup
- Image scanning configuration
- Registry authentication and permissions
- Cross-account ECR access (if needed)

### ECS Fargate
- Task definition creation
- Container port mapping
- Environment variable injection
- Secrets Manager integration for credentials
- Logging configuration
- Resource allocation (CPU, memory)
- Task placement constraints

### ECS Service Management
- Service creation and updates
- Desired task count configuration
- Load balancer integration with target groups
- Service auto-scaling policies
- Deployment strategies (rolling, blue-green)
- Health checks and container restart policies

### CI/CD Pipeline for Containers
- GitHub Actions or AWS CodePipeline
- Automated image building on code push
- Image tagging with commit hash
- Automated testing in pipeline
- Automated deployment to ECS
- Rollback strategies

### Container Security
- Image scanning for vulnerabilities
- Minimal base images (reduce attack surface)
- Non-root user in containers
- Secret management (no hardcoded secrets)
- IAM roles for container tasks
- Security group configuration

### Monitoring & Logging
- ECS CloudWatch integration
- Container log streaming
- Performance monitoring
- Resource utilization tracking
- Health check configuration

## For This Project
- Create Dockerfile for Flask backend (Python 3.11-slim, Gunicorn)
- Build and push images to ECR
- Create ECS task definitions with proper resource allocation
- Configure ECS service with ALB integration
- Set up auto-scaling policies
- Implement health checks
- Configure CloudWatch Logs streaming
- Build CI/CD pipeline for automated deployments
