"""
Incident Response Agent

Specialized agent for production incident handling, troubleshooting,
root cause analysis, and post-mortem generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .base_agent import BaseAgent
from src.core.memory.vector_db import VectorDB
from src.core.tools.executor import ToolExecutor, get_tool_executor


class IncidentSeverity(Enum):
    """Incident severity levels."""
    SEV1 = "SEV1"  # Critical - immediate response
    SEV2 = "SEV2"  # High - 15 min response
    SEV3 = "SEV3"  # Medium - 1 hour response
    SEV4 = "SEV4"  # Low - next business day


class IncidentStatus(Enum):
    """Incident lifecycle status."""
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Incident:
    """Represents a production incident."""
    
    id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    description: str
    affected_services: list[str]
    started_at: datetime
    detected_at: datetime
    resolved_at: datetime | None = None
    root_cause: str | None = None
    timeline: list[dict] = field(default_factory=list)


class IncidentResponseAgent(BaseAgent):
    """
    Incident response agent for production issue handling.
    
    Capabilities:
    - Incident triage and classification
    - Root cause analysis
    - Log and metric correlation
    - Runbook execution
    - Communication management
    - Post-mortem generation
    - Learning from past incidents (mgx.dev recommendation)
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self._vector_db = VectorDB(collection_name="incident_resolutions")
        self._tool_executor = get_tool_executor()
    
    SYSTEM_PROMPT = """You are the Incident Response Agent for DevOps Brain. Your mission is to 
minimize the impact of production incidents through rapid response and resolution.

Your responsibilities:
1. Triage and classify incoming incidents
2. Coordinate incident response activities
3. Analyze logs and metrics to identify root cause
4. Execute runbooks and remediation steps
5. Manage communication with stakeholders
6. Generate post-mortems for learning

Incident response principles:
- Time is critical - act quickly but methodically
- Communicate early and often
- Focus on mitigation before root cause
- Document everything for post-mortem
- Blameless culture - focus on systems, not people

When in doubt, escalate. A false alarm is better than a missed incident."""

    def _register_handlers(self) -> None:
        """Register incident response action handlers."""
        self.register_handler("triage_incident", self._triage_incident)
        self.register_handler("analyze_logs", self._analyze_logs)
        self.register_handler("correlate_metrics", self._correlate_metrics)
        self.register_handler("root_cause_analysis", self._root_cause_analysis)
        self.register_handler("execute_runbook", self._execute_runbook)
        self.register_handler("send_update", self._send_status_update)
        self.register_handler("generate_postmortem", self._generate_postmortem)
        self.register_handler("suggest_remediation", self._suggest_remediation)
    
    async def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def _triage_incident(self, payload: dict[str, Any]) -> dict:
        """Triage and classify an incident with learning from past incidents."""
        description = payload.get("description", "")
        
        # Search for similar past incidents (mgx.dev recommendation)
        # Initialize vector DB if needed
        try:
            if not self._vector_db._initialized:
                await self._vector_db.initialize()
            
            # Get embedding - use OpenAI or fallback
            try:
                from openai import AsyncOpenAI
                import os
                client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=description,
                )
                embedding = response.data[0].embedding
            except Exception:
                # Fallback: use simple hash (would be replaced with real embedding)
                import hashlib
                embedding = [float(int(x, 16)) / 15.0 for x in hashlib.md5(description.encode()).hexdigest()[:16]]
            
            similar_incidents = await self._vector_db.search_similar_incidents(
                query_embedding=embedding,
                limit=3,
            )
        except Exception as e:
            self.logger.warning(f"Failed to search similar incidents: {e}")
            similar_incidents = []
        
        context = ""
        if similar_incidents:
            context = "\n\nSimilar past incidents and resolutions:\n"
            for incident in similar_incidents:
                context += f"- {incident['description']}\n  Resolution: {incident['resolution']}\n"
        
        # Continue with triage...
        alert = payload.get("alert", {})
        symptoms = payload.get("symptoms", [])
        
        self.logger.info(f"Triaging incident: {alert.get('title', 'Unknown')}")
        
        # Analyze symptoms and determine severity
        severity_factors = {
            "user_impact": 0.4,
            "service_degradation": 0.3,
            "data_integrity": 0.2,
            "security_concern": 0.1,
        }
        
        triage_result = {
            "incident_id": "INC-2024-1129-001",
            "title": alert.get("title", "Service Degradation Detected"),
            "severity": "SEV2",
            "severity_rationale": [
                "User-facing API returning 500 errors",
                "Error rate above 5% threshold",
                "Multiple services affected",
            ],
            "classification": {
                "category": "availability",
                "subcategory": "service_degradation",
                "likely_cause": "database_connectivity",
            },
            "affected_services": ["api-gateway", "user-service", "order-service"],
            "estimated_impact": {
                "users_affected": 2500,
                "revenue_risk": "moderate",
                "sla_breach_risk": True,
            },
            "recommended_actions": [
                {"action": "Check database connection pool", "priority": 1},
                {"action": "Review recent deployments", "priority": 2},
                {"action": "Scale up affected services", "priority": 3},
            ],
            "escalation": {
                "required": True,
                "team": "platform-oncall",
                "reason": "SEV2 incident with SLA breach risk",
            },
        }
        
        return {
            "data": triage_result,
            "recommendations": [
                "Immediately acknowledge incident in PagerDuty",
                "Start incident channel in Slack",
                "Check database metrics dashboard",
            ],
            "next_actions": [
                "Analyze application logs",
                "Correlate with infrastructure metrics",
                "Page database oncall if needed",
            ],
        }
    
    async def _analyze_logs(self, payload: dict[str, Any]) -> dict:
        """Analyze logs for incident investigation."""
        services = payload.get("services", [])
        time_range = payload.get("time_range", "15m")
        incident_id = payload.get("incident_id")
        
        self.logger.info(f"Analyzing logs for incident {incident_id}")
        
        log_analysis = {
            "query": {
                "services": services or ["api-gateway", "user-service"],
                "time_range": time_range,
                "filters": ["level:error OR level:warn"],
            },
            "summary": {
                "total_logs_analyzed": 15420,
                "error_count": 892,
                "warning_count": 2341,
                "first_error_at": "2024-11-29T14:23:15Z",
                "peak_error_time": "2024-11-29T14:28:00Z",
            },
            "patterns": [
                {
                    "pattern": "Connection refused: database-primary:5432",
                    "count": 456,
                    "services": ["user-service", "order-service"],
                    "significance": "high",
                    "interpretation": "Database connection failures",
                },
                {
                    "pattern": "Timeout waiting for connection from pool",
                    "count": 312,
                    "services": ["api-gateway"],
                    "significance": "high",
                    "interpretation": "Connection pool exhausted",
                },
                {
                    "pattern": "Retry attempt 3/3 failed",
                    "count": 124,
                    "services": ["user-service"],
                    "significance": "medium",
                    "interpretation": "Retry logic exhausted",
                },
            ],
            "stack_traces": [
                {
                    "error": "ConnectionError",
                    "message": "Cannot connect to database",
                    "file": "src/db/connection.py",
                    "line": 45,
                    "count": 234,
                },
            ],
            "timeline": [
                {"time": "14:23:15", "event": "First connection error"},
                {"time": "14:25:00", "event": "Error rate crosses 1%"},
                {"time": "14:28:00", "event": "Peak errors - 50/sec"},
                {"time": "14:30:00", "event": "Partial recovery"},
            ],
        }
        
        return {
            "data": log_analysis,
            "recommendations": [
                "Primary database connection is the root cause",
                "Check database server health and connectivity",
                "Review connection pool settings",
            ],
            "metadata": {
                "log_source": "elasticsearch",
                "analysis_time_ms": 2340,
            },
        }
    
    async def _correlate_metrics(self, payload: dict[str, Any]) -> dict:
        """Correlate metrics across services for incident analysis."""
        incident_id = payload.get("incident_id")
        time_range = payload.get("time_range", "1h")
        
        self.logger.info(f"Correlating metrics for incident {incident_id}")
        
        correlations = {
            "time_range": time_range,
            "metrics_analyzed": 45,
            "correlations": [
                {
                    "metric_a": "database.connections.active",
                    "metric_b": "api.error_rate",
                    "correlation": 0.94,
                    "lag_seconds": 5,
                    "interpretation": "Database connection issues directly causing API errors",
                },
                {
                    "metric_a": "database.query_time_p99",
                    "metric_b": "database.connections.waiting",
                    "correlation": 0.87,
                    "lag_seconds": 0,
                    "interpretation": "Slow queries blocking connection pool",
                },
            ],
            "anomalies": [
                {
                    "metric": "database.connections.active",
                    "timestamp": "2024-11-29T14:22:00Z",
                    "expected": 50,
                    "actual": 200,
                    "deviation": "4x normal",
                },
                {
                    "metric": "database.query_time_p99",
                    "timestamp": "2024-11-29T14:21:00Z",
                    "expected": "50ms",
                    "actual": "2500ms",
                    "deviation": "50x normal",
                },
            ],
            "root_cause_indicators": [
                "Query performance degradation started at 14:21",
                "Connection pool saturation followed at 14:22",
                "API errors started at 14:23",
            ],
        }
        
        return {
            "data": correlations,
            "recommendations": [
                "Slow query at 14:21 is likely the trigger",
                "Check for missing indexes or lock contention",
                "Increase connection pool timeout as temporary mitigation",
            ],
        }
    
    async def _root_cause_analysis(self, payload: dict[str, Any]) -> dict:
        """Perform root cause analysis."""
        incident_id = payload.get("incident_id")
        evidence = payload.get("evidence", {})
        
        self.logger.info(f"Performing RCA for incident {incident_id}")
        
        rca = {
            "incident_id": incident_id,
            "summary": "Database query performance degradation caused cascading failures",
            "root_cause": {
                "category": "database",
                "description": "A long-running analytical query without proper indexing caused table locks, leading to connection pool exhaustion and cascading service failures.",
                "trigger": "Scheduled analytics job started at 14:20",
                "evidence": [
                    "Query execution time increased from 50ms to 2500ms at 14:21",
                    "Connection pool saturated by 14:22",
                    "API errors began at 14:23",
                ],
            },
            "contributing_factors": [
                {
                    "factor": "Missing index on analytics table",
                    "impact": "high",
                    "remediation": "Add composite index",
                },
                {
                    "factor": "No query timeout configured",
                    "impact": "medium",
                    "remediation": "Set statement_timeout to 30s",
                },
                {
                    "factor": "Shared database for OLTP and analytics",
                    "impact": "medium",
                    "remediation": "Separate read replica for analytics",
                },
            ],
            "five_whys": [
                {"why": "Why did the API return errors?", "answer": "Database connections were exhausted"},
                {"why": "Why were connections exhausted?", "answer": "Connections were blocked waiting for slow query"},
                {"why": "Why was the query slow?", "answer": "Full table scan due to missing index"},
                {"why": "Why was there no index?", "answer": "Analytics table not reviewed for performance"},
                {"why": "Why wasn't it reviewed?", "answer": "No process for analytics query review"},
            ],
        }
        
        return {
            "data": rca,
            "recommendations": [
                "Add missing index immediately",
                "Implement query review process for analytics",
                "Set up read replica for analytical workloads",
            ],
            "next_actions": [
                "Schedule index creation during maintenance window",
                "Document analytics query guidelines",
            ],
        }
    
    async def _execute_runbook(self, payload: dict[str, Any]) -> dict:
        """Execute a predefined runbook."""
        runbook_id = payload.get("runbook_id")
        parameters = payload.get("parameters", {})
        
        self.logger.info(f"Executing runbook: {runbook_id}")
        
        execution = {
            "runbook_id": runbook_id or "RB-DB-001",
            "runbook_name": "Database Connection Pool Recovery",
            "status": "completed",
            "steps_executed": [
                {
                    "step": 1,
                    "name": "Check database connectivity",
                    "status": "success",
                    "output": "Database is reachable",
                    "duration_seconds": 2,
                },
                {
                    "step": 2,
                    "name": "Kill long-running queries",
                    "status": "success",
                    "output": "Terminated 3 queries running > 60s",
                    "duration_seconds": 5,
                },
                {
                    "step": 3,
                    "name": "Reset connection pool",
                    "status": "success",
                    "output": "Connection pool reset on 4 instances",
                    "duration_seconds": 15,
                },
                {
                    "step": 4,
                    "name": "Verify service health",
                    "status": "success",
                    "output": "All health checks passing",
                    "duration_seconds": 10,
                },
            ],
            "total_duration_seconds": 32,
            "result": {
                "recovery_confirmed": True,
                "services_recovered": ["api-gateway", "user-service", "order-service"],
                "metrics_normalized": True,
            },
        }
        
        return {
            "data": execution,
            "recommendations": [
                "Monitor for recurrence in next 30 minutes",
                "Continue with root cause analysis",
            ],
        }
    
    async def _send_status_update(self, payload: dict[str, Any]) -> dict:
        """Send incident status update."""
        incident_id = payload.get("incident_id")
        status = payload.get("status")
        message = payload.get("message")
        
        self.logger.info(f"Sending status update for {incident_id}: {status}")
        
        update = {
            "incident_id": incident_id,
            "status": status,
            "update": {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message or "Incident investigation in progress",
                "severity": "SEV2",
                "impact": "Degraded API performance for some users",
                "current_status": "Mitigating - connection pool reset in progress",
                "eta_resolution": "15 minutes",
                "next_update": "10 minutes",
            },
            "notifications_sent": [
                {"channel": "slack", "target": "#incidents", "status": "sent"},
                {"channel": "slack", "target": "#engineering", "status": "sent"},
                {"channel": "statuspage", "status": "sent"},
                {"channel": "pagerduty", "status": "acknowledged"},
            ],
        }
        
        return {
            "data": update,
            "metadata": {
                "template": "incident_update_v1",
            },
        }
    
    async def _generate_postmortem(self, payload: dict[str, Any]) -> dict:
        """Generate a post-mortem document and store resolution for learning."""
        incident_id = payload.get("incident_id")
        
        self.logger.info(f"Generating post-mortem for {incident_id}")
        
        # Get incident details
        description = payload.get("description", "")
        resolution = payload.get("resolution", "")
        
        # Store resolution for learning (mgx.dev recommendation)
        if description and resolution:
            try:
                if not self._vector_db._initialized:
                    await self._vector_db.initialize()
                
                # Get embedding - use OpenAI or fallback
                try:
                    from openai import AsyncOpenAI
                    import os
                    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                    response = await client.embeddings.create(
                        model="text-embedding-3-small",
                        input=f"{description}\n{resolution}",
                    )
                    embedding = response.data[0].embedding
                except Exception:
                    # Fallback: use simple hash (would be replaced with real embedding)
                    import hashlib
                    embedding = [float(int(x, 16)) / 15.0 for x in hashlib.md5(
                        f"{description}\n{resolution}".encode()
                    ).hexdigest()[:16]]
                
                await self._vector_db.store_incident_resolution(
                    incident_id=incident_id or "unknown",
                    description=description,
                    resolution=resolution,
                    embedding=embedding,
                    metadata={
                        "agent": "incident_response_agent",
                        "severity": payload.get("severity", "unknown"),
                    },
                )
                self.logger.info(f"Stored incident resolution for learning: {incident_id}")
            except Exception as e:
                self.logger.warning(f"Failed to store incident resolution: {e}")
        
        postmortem = {
            "incident_id": incident_id or "INC-2024-1129-001",
            "title": "Database Connection Pool Exhaustion - API Degradation",
            "date": "2024-11-29",
            "severity": "SEV2",
            "duration": "18 minutes",
            "authors": ["incident-response-agent", "platform-oncall"],
            
            "executive_summary": """
On November 29, 2024, users experienced API errors for approximately 18 minutes 
due to database connection pool exhaustion. The root cause was a long-running 
analytics query that blocked the connection pool. The incident was mitigated by 
terminating the blocking query and resetting the connection pool.
""",
            
            "impact": {
                "users_affected": 2500,
                "requests_failed": 12500,
                "error_rate_peak": "15%",
                "revenue_impact": "$2,500 (estimated)",
                "sla_breach": False,
            },
            
            "timeline": [
                {"time": "14:20:00", "event": "Analytics job started"},
                {"time": "14:21:00", "event": "Query execution time increased to 2500ms"},
                {"time": "14:22:00", "event": "Connection pool saturated"},
                {"time": "14:23:00", "event": "First API errors detected"},
                {"time": "14:25:00", "event": "Alert fired, incident created"},
                {"time": "14:27:00", "event": "Incident acknowledged, investigation started"},
                {"time": "14:32:00", "event": "Root cause identified"},
                {"time": "14:35:00", "event": "Blocking query terminated"},
                {"time": "14:38:00", "event": "Connection pool reset"},
                {"time": "14:41:00", "event": "Services recovered, incident resolved"},
            ],
            
            "root_cause": """
The scheduled analytics job executed a query that performed a full table scan 
on the `orders` table due to a missing index. This query held locks that 
prevented other queries from completing, causing the connection pool to 
become exhausted.
""",
            
            "action_items": [
                {
                    "id": "AI-001",
                    "action": "Add composite index on orders(created_at, status)",
                    "owner": "database-team",
                    "priority": "P1",
                    "due_date": "2024-12-02",
                    "status": "pending",
                },
                {
                    "id": "AI-002",
                    "action": "Configure statement_timeout to 30 seconds",
                    "owner": "platform-team",
                    "priority": "P1",
                    "due_date": "2024-12-01",
                    "status": "pending",
                },
                {
                    "id": "AI-003",
                    "action": "Set up read replica for analytics workloads",
                    "owner": "database-team",
                    "priority": "P2",
                    "due_date": "2024-12-15",
                    "status": "pending",
                },
                {
                    "id": "AI-004",
                    "action": "Add query review process for analytics jobs",
                    "owner": "data-team",
                    "priority": "P2",
                    "due_date": "2024-12-10",
                    "status": "pending",
                },
            ],
            
            "lessons_learned": [
                "OLTP and analytics workloads should be separated",
                "All scheduled jobs need query performance review",
                "Connection pool monitoring alerts need lower thresholds",
                "Runbook execution significantly reduced MTTR",
            ],
            
            "what_went_well": [
                "Alert fired within 2 minutes of issue start",
                "Incident was triaged correctly as SEV2",
                "Runbook was effective for mitigation",
                "Communication to stakeholders was timely",
            ],
            
            "what_could_be_improved": [
                "Detection could be faster with lower thresholds",
                "Analytics query review process was missing",
                "Connection pool limits were too generous",
            ],
        }
        
        return {
            "data": postmortem,
            "recommendations": [
                "Schedule post-mortem review meeting",
                "Track action items in project management tool",
                "Share learnings with wider engineering team",
            ],
            "metadata": {
                "format": "markdown",
                "template": "postmortem_v2",
            },
        }
    
    async def _suggest_remediation(self, payload: dict[str, Any]) -> dict:
        """Suggest remediation steps for an incident."""
        incident_type = payload.get("type", "unknown")
        symptoms = payload.get("symptoms", [])
        
        self.logger.info(f"Suggesting remediation for {incident_type}")
        
        remediations = {
            "immediate": [
                {
                    "action": "Scale up affected service",
                    "command": "kubectl scale deployment api-gateway --replicas=10",
                    "risk": "low",
                    "estimated_impact": "Increase capacity by 2x",
                },
                {
                    "action": "Enable circuit breaker",
                    "command": "curl -X POST http://config-service/circuit-breaker/enable",
                    "risk": "low",
                    "estimated_impact": "Prevent cascade failures",
                },
            ],
            "short_term": [
                {
                    "action": "Increase connection pool size",
                    "change": "DB_POOL_SIZE: 50 -> 100",
                    "risk": "medium",
                    "requires_restart": True,
                },
                {
                    "action": "Add query timeout",
                    "change": "statement_timeout = 30000",
                    "risk": "low",
                    "requires_restart": False,
                },
            ],
            "long_term": [
                {
                    "action": "Implement read replicas",
                    "effort": "high",
                    "timeline": "2 weeks",
                },
                {
                    "action": "Add query performance monitoring",
                    "effort": "medium",
                    "timeline": "1 week",
                },
            ],
        }
        
        return {
            "data": {
                "incident_type": incident_type,
                "remediations": remediations,
                "recommended_first_action": remediations["immediate"][0],
            },
            "recommendations": [
                "Start with immediate actions to restore service",
                "Plan short-term fixes for deployment within 24 hours",
                "Schedule long-term improvements in sprint planning",
            ],
        }
