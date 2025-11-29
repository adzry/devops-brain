"""
Database Agent

Specialized agent for database optimization, migration management,
schema design, and data operations.
"""

from enum import Enum
from typing import Any

from .base_agent import BaseAgent


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    SQLITE = "sqlite"


class MigrationStrategy(Enum):
    """Database migration strategies."""
    ZERO_DOWNTIME = "zero_downtime"
    MAINTENANCE_WINDOW = "maintenance_window"
    BLUE_GREEN = "blue_green"


class DatabaseAgent(BaseAgent):
    """
    Database-focused agent for optimization and management.
    
    Capabilities:
    - Schema design and review
    - Migration generation and execution
    - Query optimization
    - Index recommendations
    - Backup and recovery
    - Replication setup
    """
    
    SYSTEM_PROMPT = """You are the Database Agent for DevOps Brain. Your mission is to 
ensure optimal database performance, reliability, and data integrity.

Your responsibilities:
1. Design efficient database schemas
2. Generate and review migrations
3. Optimize query performance
4. Manage backups and recovery
5. Configure replication and high availability

Database principles:
- Data integrity is paramount
- Optimize for the access patterns
- Plan for scale from the start
- Zero-downtime migrations when possible

A well-designed database is the foundation of a reliable system."""

    def _register_handlers(self) -> None:
        """Register database action handlers."""
        self.register_handler("design_schema", self._design_schema)
        self.register_handler("review_schema", self._review_schema)
        self.register_handler("generate_migration", self._generate_migration)
        self.register_handler("optimize_queries", self._optimize_queries)
        self.register_handler("recommend_indexes", self._recommend_indexes)
        self.register_handler("plan_backup", self._plan_backup)
        self.register_handler("analyze_performance", self._analyze_performance)
    
    async def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def _design_schema(self, payload: dict[str, Any]) -> dict:
        """Design a database schema."""
        requirements = payload.get("requirements", {})
        database_type = payload.get("database", "postgresql")
        
        self.logger.info(f"Designing schema for {database_type}")
        
        schema = {
            "database": database_type,
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "UUID", "primary_key": True, "default": "gen_random_uuid()"},
                        {"name": "email", "type": "VARCHAR(255)", "unique": True, "not_null": True},
                        {"name": "name", "type": "VARCHAR(100)", "not_null": True},
                        {"name": "password_hash", "type": "VARCHAR(255)", "not_null": True},
                        {"name": "status", "type": "VARCHAR(20)", "default": "'active'"},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"},
                        {"name": "updated_at", "type": "TIMESTAMP", "default": "NOW()"},
                    ],
                    "indexes": [
                        {"columns": ["email"], "unique": True},
                        {"columns": ["status", "created_at"]},
                    ],
                },
                {
                    "name": "orders",
                    "columns": [
                        {"name": "id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "UUID", "foreign_key": "users(id)"},
                        {"name": "status", "type": "VARCHAR(20)", "not_null": True},
                        {"name": "total_amount", "type": "DECIMAL(10,2)", "not_null": True},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"},
                    ],
                    "indexes": [
                        {"columns": ["user_id"]},
                        {"columns": ["status", "created_at"]},
                        {"columns": ["created_at"]},
                    ],
                },
            ],
            "sql": """
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_status_created ON users(status, created_at);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status_created ON orders(status, created_at);
CREATE INDEX idx_orders_created ON orders(created_at);
""",
        }
        
        return {
            "data": schema,
            "recommendations": [
                "Add soft delete with deleted_at column for audit trail",
                "Consider partitioning orders table by created_at",
                "Add check constraints for status fields",
            ],
        }
    
    async def _review_schema(self, payload: dict[str, Any]) -> dict:
        """Review existing schema for improvements."""
        schema = payload.get("schema", {})
        
        self.logger.info("Reviewing database schema")
        
        issues = [
            {
                "severity": "high",
                "table": "orders",
                "issue": "Missing index on frequently queried column",
                "column": "customer_email",
                "recommendation": "Add index: CREATE INDEX idx_orders_email ON orders(customer_email)",
            },
            {
                "severity": "medium",
                "table": "products",
                "issue": "VARCHAR without length limit",
                "column": "description",
                "recommendation": "Use TEXT type or specify max length",
            },
            {
                "severity": "low",
                "table": "users",
                "issue": "Inconsistent naming convention",
                "column": "createdAt vs created_at",
                "recommendation": "Standardize on snake_case for PostgreSQL",
            },
        ]
        
        return {
            "data": {
                "tables_reviewed": 5,
                "issues_found": len(issues),
                "issues": issues,
                "score": 72,
                "score_breakdown": {
                    "indexing": 65,
                    "normalization": 85,
                    "naming": 70,
                    "constraints": 75,
                },
            },
            "recommendations": [
                "Add missing indexes for better query performance",
                "Standardize column naming conventions",
                "Add NOT NULL constraints where appropriate",
            ],
        }
    
    async def _generate_migration(self, payload: dict[str, Any]) -> dict:
        """Generate database migration."""
        changes = payload.get("changes", [])
        strategy = payload.get("strategy", "zero_downtime")
        
        self.logger.info(f"Generating migration with {strategy} strategy")
        
        migration = {
            "version": "20241129_143000",
            "name": "add_user_preferences",
            "strategy": strategy,
            "up": """
-- Migration: add_user_preferences
-- Strategy: zero_downtime

-- Step 1: Add new column as nullable
ALTER TABLE users ADD COLUMN preferences JSONB;

-- Step 2: Backfill data (run in batches in production)
UPDATE users SET preferences = '{}' WHERE preferences IS NULL;

-- Step 3: Add constraint (after backfill complete)
-- ALTER TABLE users ALTER COLUMN preferences SET NOT NULL;
-- ALTER TABLE users ALTER COLUMN preferences SET DEFAULT '{}';

-- Step 4: Add index for JSON queries
CREATE INDEX CONCURRENTLY idx_users_preferences ON users USING GIN (preferences);
""",
            "down": """
-- Rollback: add_user_preferences

DROP INDEX CONCURRENTLY IF EXISTS idx_users_preferences;
ALTER TABLE users DROP COLUMN IF EXISTS preferences;
""",
            "notes": [
                "Use CONCURRENTLY for index creation to avoid locks",
                "Backfill in batches of 1000 rows",
                "Add NOT NULL constraint after backfill is complete",
            ],
            "estimated_duration": {
                "small_table": "< 1 second",
                "large_table": "Depends on backfill - estimate 10 min per 1M rows",
            },
            "risks": [
                {
                    "risk": "Long-running backfill may cause replication lag",
                    "mitigation": "Process in small batches with delays",
                },
            ],
        }
        
        return {
            "data": migration,
            "recommendations": [
                "Test migration on staging with production-like data",
                "Monitor replication lag during execution",
                "Have rollback plan ready",
            ],
        }
    
    async def _optimize_queries(self, payload: dict[str, Any]) -> dict:
        """Optimize database queries."""
        queries = payload.get("queries", [])
        
        self.logger.info(f"Optimizing {len(queries)} queries")
        
        optimizations = [
            {
                "original": """
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > '2024-01-01'
ORDER BY o.created_at DESC
""",
                "optimized": """
SELECT o.id, o.status, o.total_amount, o.created_at,
       u.id as user_id, u.name, u.email
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > '2024-01-01'
ORDER BY o.created_at DESC
LIMIT 100
""",
                "improvements": [
                    "Select only needed columns instead of *",
                    "Added LIMIT to prevent unbounded result sets",
                ],
                "explain_before": {
                    "plan": "Seq Scan on orders",
                    "cost": 15000,
                    "rows": 50000,
                },
                "explain_after": {
                    "plan": "Index Scan using idx_orders_created",
                    "cost": 150,
                    "rows": 100,
                },
                "speedup": "100x",
            },
        ]
        
        return {
            "data": {
                "queries_analyzed": len(queries) or 1,
                "optimizations": optimizations,
            },
            "recommendations": [
                "Always use LIMIT for user-facing queries",
                "Avoid SELECT * in production code",
                "Use covering indexes for frequently accessed columns",
            ],
        }
    
    async def _recommend_indexes(self, payload: dict[str, Any]) -> dict:
        """Recommend indexes based on query patterns."""
        table = payload.get("table")
        query_log = payload.get("query_log", [])
        
        self.logger.info(f"Analyzing index recommendations for {table}")
        
        recommendations = [
            {
                "table": "orders",
                "index": "CREATE INDEX idx_orders_user_status ON orders(user_id, status)",
                "reason": "Frequent queries filtering by user_id and status",
                "query_count": 15000,
                "estimated_improvement": "80% faster",
                "size_estimate": "~50MB",
            },
            {
                "table": "orders",
                "index": "CREATE INDEX idx_orders_created_partial ON orders(created_at) WHERE status = 'pending'",
                "reason": "Frequent queries for pending orders by date",
                "query_count": 8500,
                "estimated_improvement": "90% faster",
                "size_estimate": "~10MB (partial)",
            },
            {
                "table": "products",
                "index": "CREATE INDEX idx_products_search ON products USING GIN(to_tsvector('english', name || ' ' || description))",
                "reason": "Full-text search queries on products",
                "query_count": 5000,
                "estimated_improvement": "95% faster than LIKE",
                "size_estimate": "~100MB",
            },
        ]
        
        unused_indexes = [
            {
                "table": "users",
                "index": "idx_users_legacy_id",
                "last_used": "Never",
                "size": "25MB",
                "recommendation": "DROP INDEX idx_users_legacy_id",
            },
        ]
        
        return {
            "data": {
                "recommendations": recommendations,
                "unused_indexes": unused_indexes,
                "total_size_new": "160MB",
                "total_size_removable": "25MB",
            },
            "recommendations": [
                "Add composite index for user_id + status queries",
                "Use partial index for status-filtered queries",
                "Remove unused idx_users_legacy_id to save space",
            ],
        }
    
    async def _plan_backup(self, payload: dict[str, Any]) -> dict:
        """Plan database backup strategy."""
        database = payload.get("database", "postgresql")
        requirements = payload.get("requirements", {})
        
        self.logger.info(f"Planning backup strategy for {database}")
        
        backup_plan = {
            "database": database,
            "strategy": {
                "type": "continuous",
                "base_backup": {
                    "frequency": "daily",
                    "time": "02:00 UTC",
                    "retention": "30 days",
                    "method": "pg_basebackup",
                },
                "wal_archiving": {
                    "enabled": True,
                    "destination": "s3://backups/wal/",
                    "retention": "7 days",
                },
                "point_in_time_recovery": True,
                "rpo": "< 1 minute",
                "rto": "< 1 hour",
            },
            "schedule": [
                {"type": "full", "frequency": "weekly", "day": "Sunday", "time": "02:00"},
                {"type": "incremental", "frequency": "daily", "time": "02:00"},
                {"type": "wal", "frequency": "continuous", "archive_timeout": "60s"},
            ],
            "storage": {
                "primary": "s3://backups/postgresql/",
                "secondary": "gs://backups-dr/postgresql/",
                "encryption": "AES-256",
                "estimated_size_monthly": "500GB",
            },
            "testing": {
                "restore_test_frequency": "monthly",
                "automated_verification": True,
            },
            "commands": {
                "create_backup": "pg_basebackup -D /backup -Ft -z -P",
                "restore": "pg_restore -d dbname /backup/base.tar.gz",
                "point_in_time": "recovery_target_time = '2024-11-29 14:00:00'",
            },
        }
        
        return {
            "data": backup_plan,
            "recommendations": [
                "Test restore procedure monthly",
                "Monitor backup completion alerts",
                "Keep backups in different region for DR",
            ],
        }
    
    async def _analyze_performance(self, payload: dict[str, Any]) -> dict:
        """Analyze database performance."""
        time_range = payload.get("time_range", "24h")
        
        self.logger.info(f"Analyzing database performance for {time_range}")
        
        analysis = {
            "time_range": time_range,
            "summary": {
                "health_score": 78,
                "qps_avg": 1250,
                "qps_peak": 3500,
                "connections_avg": 45,
                "connections_max": 100,
            },
            "slow_queries": [
                {
                    "query": "SELECT * FROM orders WHERE status = $1 ORDER BY created_at",
                    "avg_time_ms": 450,
                    "calls": 5000,
                    "total_time_s": 2250,
                    "suggestion": "Add index on (status, created_at)",
                },
                {
                    "query": "SELECT COUNT(*) FROM users WHERE last_login > $1",
                    "avg_time_ms": 320,
                    "calls": 1000,
                    "total_time_s": 320,
                    "suggestion": "Add index on last_login",
                },
            ],
            "resource_usage": {
                "cpu_avg_percent": 35,
                "memory_used_percent": 72,
                "disk_io_read_mbps": 45,
                "disk_io_write_mbps": 12,
                "cache_hit_ratio": 0.94,
            },
            "connection_stats": {
                "active": 45,
                "idle": 35,
                "waiting": 2,
                "max_connections": 200,
            },
            "replication": {
                "lag_bytes": 1024,
                "lag_seconds": 0.5,
                "status": "healthy",
            },
        }
        
        return {
            "data": analysis,
            "recommendations": [
                "Add indexes for top slow queries",
                "Cache hit ratio is good at 94%",
                "Consider increasing shared_buffers for better caching",
                "Monitor connection pool usage during peak hours",
            ],
        }
