# Database Design & MySQL

## Overview
Relational database design, MySQL implementation, optimization, and integration with Python ORM frameworks.

## Key Skills

### Database Design Fundamentals
- Schema design and normalization (1NF, 2NF, 3NF)
- Entity-relationship modeling
- Primary keys and foreign key constraints
- Indexes (B-tree, hash, composite)
- Data types selection (INT, VARCHAR, DATETIME, JSON, ENUM)
- Constraints (NOT NULL, UNIQUE, CHECK, DEFAULT)

### MySQL Configuration
- MySQL 8.0 features and compatibility
- Configuration parameters (my.cnf)
- Connection pooling settings
- Query optimization parameters
- Buffer pool configuration
- Slow query log

### Transaction Management
- ACID properties (Atomicity, Consistency, Isolation, Durability)
- Isolation levels (READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE)
- Transaction control (BEGIN, COMMIT, ROLLBACK)
- Deadlock detection and handling
- Pessimistic vs optimistic locking

### Query Optimization
- Query execution plans (EXPLAIN)
- Index usage and selection
- Join optimization
- Subquery optimization
- Aggregate function optimization
- Query performance tuning

### Replication & High Availability
- Master-slave replication
- Multi-AZ failover
- Binary logging
- Replication lag monitoring
- Backup and recovery strategies

### Security
- User management and privileges
- Encryption at-rest (TLS)
- Encryption in-transit (SSL/TLS)
- Firewall and access control
- Audit logging

### Backup & Recovery
- Automated backup strategies
- Point-in-time recovery
- Backup retention policies
- Disaster recovery planning
- RDS automated backups and snapshots

### SQLAlchemy ORM Integration
- Model definition and relationships
- Query API (filter, order_by, join)
- Eager loading and lazy loading
- Relationship cascades
- Bulk operations
- Session management

## For This Project
- Design 15+ database tables for all entities
- Implement proper indexing for performance
- Set up foreign key relationships with cascades
- Configure connection pooling (pool_size=20, max_overflow=40)
- Implement soft-delete patterns
- Create efficient queries for attendance tracking
- Configure MySQL for SERIALIZABLE isolation (check-in/out)
- Set up automated RDS backups and monitoring
- Optimize queries for real-time dashboard
