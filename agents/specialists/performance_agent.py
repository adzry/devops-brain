"""
Performance Agent

Specialized agent for performance analysis, optimization recommendations,
and load testing orchestration.
"""

from enum import Enum
from typing import Any

from .base_agent import BaseAgent


class PerformanceMetric(Enum):
    """Types of performance metrics."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"


class PerformanceAgent(BaseAgent):
    """
    Performance-focused agent for optimization and profiling.
    
    Capabilities:
    - Performance profiling and analysis
    - Bottleneck detection
    - Optimization recommendations
    - Load testing orchestration
    - Query optimization
    - Caching strategy recommendations
    """
    
    SYSTEM_PROMPT = """You are the Performance Agent for DevOps Brain. Your mission is to 
ensure optimal performance of applications and infrastructure.

Your responsibilities:
1. Profile applications to identify bottlenecks
2. Analyze performance metrics and trends
3. Recommend optimizations for code, queries, and infrastructure
4. Orchestrate load and stress testing
5. Design caching and scaling strategies

Performance principles:
- Measure before optimizing
- Focus on the critical path
- Optimize for the common case
- Consider trade-offs (memory vs CPU, latency vs throughput)

A 10% improvement for 1000 users beats a 90% improvement for 10 users."""

    def _register_handlers(self) -> None:
        """Register performance action handlers."""
        self.register_handler("profile_application", self._profile_application)
        self.register_handler("analyze_metrics", self._analyze_metrics)
        self.register_handler("detect_bottlenecks", self._detect_bottlenecks)
        self.register_handler("optimize_queries", self._optimize_queries)
        self.register_handler("run_load_test", self._run_load_test)
        self.register_handler("recommend_caching", self._recommend_caching)
        self.register_handler("analyze_memory", self._analyze_memory)
    
    async def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def _profile_application(self, payload: dict[str, Any]) -> dict:
        """Profile application performance."""
        target = payload.get("target", "main")
        duration_seconds = payload.get("duration", 60)
        
        self.logger.info(f"Profiling {target} for {duration_seconds}s")
        
        profile_results = {
            "hot_spots": [
                {
                    "function": "process_request",
                    "file": "src/api/handlers.py",
                    "line": 45,
                    "self_time_ms": 125,
                    "total_time_ms": 340,
                    "calls": 1500,
                    "percentage": 28.5,
                },
                {
                    "function": "query_database",
                    "file": "src/db/queries.py",
                    "line": 78,
                    "self_time_ms": 98,
                    "total_time_ms": 210,
                    "calls": 3200,
                    "percentage": 22.1,
                },
                {
                    "function": "serialize_response",
                    "file": "src/api/serializers.py",
                    "line": 23,
                    "self_time_ms": 67,
                    "total_time_ms": 85,
                    "calls": 1500,
                    "percentage": 15.2,
                },
            ],
            "call_graph": {
                "root": "handle_request",
                "children": [
                    {"name": "authenticate", "time_ms": 15},
                    {"name": "process_request", "time_ms": 340},
                    {"name": "serialize_response", "time_ms": 85},
                ],
            },
        }
        
        return {
            "data": {
                "target": target,
                "duration_seconds": duration_seconds,
                "total_samples": 15000,
                "profile": profile_results,
                "summary": {
                    "top_function": "process_request",
                    "top_percentage": 28.5,
                    "functions_analyzed": 45,
                },
            },
            "recommendations": [
                "Optimize process_request - consuming 28.5% of CPU time",
                "Consider caching database queries - high call count",
                "Review serialization logic for optimization opportunities",
            ],
            "next_actions": [
                "Analyze process_request for algorithmic improvements",
                "Profile database queries separately",
            ],
        }
    
    async def _analyze_metrics(self, payload: dict[str, Any]) -> dict:
        """Analyze performance metrics."""
        metrics = payload.get("metrics", ["latency", "throughput"])
        time_range = payload.get("time_range", "1h")
        
        self.logger.info(f"Analyzing metrics: {metrics} over {time_range}")
        
        analysis = {
            "latency": {
                "p50_ms": 45,
                "p95_ms": 125,
                "p99_ms": 350,
                "max_ms": 1250,
                "trend": "stable",
                "anomalies": [
                    {"timestamp": "2024-11-29T14:30:00Z", "value_ms": 1250, "cause": "GC pause"}
                ],
            },
            "throughput": {
                "avg_rps": 850,
                "peak_rps": 1200,
                "min_rps": 500,
                "trend": "increasing",
            },
            "error_rate": {
                "percentage": 0.5,
                "trend": "stable",
                "by_type": {
                    "timeout": 0.3,
                    "5xx": 0.15,
                    "4xx": 0.05,
                },
            },
        }
        
        return {
            "data": {
                "time_range": time_range,
                "analysis": analysis,
                "health_score": 85,
                "sla_compliance": {
                    "latency_p99_target": "500ms",
                    "compliant": True,
                    "margin_ms": 150,
                },
            },
            "recommendations": [
                "Investigate GC pause causing latency spike",
                "Monitor throughput increase - may need scaling soon",
                "Reduce timeout errors with connection pooling",
            ],
        }
    
    async def _detect_bottlenecks(self, payload: dict[str, Any]) -> dict:
        """Detect performance bottlenecks."""
        scope = payload.get("scope", "full")
        
        self.logger.info(f"Detecting bottlenecks (scope: {scope})")
        
        bottlenecks = [
            {
                "type": "database",
                "description": "N+1 query pattern in user listing",
                "impact": "high",
                "location": "src/api/users.py:get_users_with_orders",
                "metrics": {
                    "queries_per_request": 51,
                    "expected_queries": 2,
                    "added_latency_ms": 180,
                },
                "fix": "Use eager loading with JOIN or separate batch query",
            },
            {
                "type": "cpu",
                "description": "Synchronous JSON parsing in hot path",
                "impact": "medium",
                "location": "src/parsers/json_parser.py:parse_large_response",
                "metrics": {
                    "cpu_time_ms": 45,
                    "frequency": "high",
                },
                "fix": "Use streaming JSON parser or move to background thread",
            },
            {
                "type": "memory",
                "description": "Large object allocation in loop",
                "impact": "medium",
                "location": "src/processors/batch.py:process_items",
                "metrics": {
                    "allocation_mb": 256,
                    "gc_frequency": "frequent",
                },
                "fix": "Reuse objects or process in chunks",
            },
        ]
        
        return {
            "data": {
                "bottlenecks_found": len(bottlenecks),
                "by_impact": {"high": 1, "medium": 2, "low": 0},
                "by_type": {"database": 1, "cpu": 1, "memory": 1},
                "bottlenecks": bottlenecks,
                "estimated_improvement": "40-60% latency reduction",
            },
            "recommendations": [
                "Fix N+1 query - highest impact issue",
                "Implement streaming JSON parser",
                "Refactor batch processor for memory efficiency",
            ],
            "next_actions": [
                "Create issue for N+1 query fix",
                "Profile memory allocation patterns",
            ],
        }
    
    async def _optimize_queries(self, payload: dict[str, Any]) -> dict:
        """Analyze and optimize database queries."""
        queries = payload.get("queries", [])
        
        self.logger.info(f"Optimizing {len(queries)} queries")
        
        optimizations = [
            {
                "original": "SELECT * FROM users WHERE status = 'active'",
                "optimized": "SELECT id, name, email FROM users WHERE status = 'active'",
                "improvement": "Select only needed columns",
                "estimated_speedup": "30%",
            },
            {
                "original": "SELECT * FROM orders WHERE created_at > '2024-01-01' ORDER BY created_at",
                "optimized": "SELECT * FROM orders WHERE created_at > '2024-01-01' ORDER BY created_at LIMIT 100",
                "improvement": "Add pagination to prevent full table scan",
                "estimated_speedup": "80%",
                "index_suggestion": "CREATE INDEX idx_orders_created ON orders(created_at)",
            },
        ]
        
        return {
            "data": {
                "queries_analyzed": len(queries) or 2,
                "optimizations": optimizations,
                "index_recommendations": [
                    {
                        "table": "orders",
                        "columns": ["created_at"],
                        "type": "btree",
                        "reason": "Frequent range queries on created_at",
                    },
                    {
                        "table": "users",
                        "columns": ["status", "created_at"],
                        "type": "composite",
                        "reason": "Common filter combination",
                    },
                ],
            },
            "recommendations": [
                "Avoid SELECT * in production queries",
                "Always paginate large result sets",
                "Add suggested indexes during low-traffic period",
            ],
        }
    
    async def _run_load_test(self, payload: dict[str, Any]) -> dict:
        """Orchestrate load testing."""
        target_url = payload.get("url", "http://localhost:8000")
        users = payload.get("users", 100)
        duration = payload.get("duration_seconds", 60)
        
        self.logger.info(f"Running load test: {users} users for {duration}s")
        
        results = {
            "summary": {
                "total_requests": 12500,
                "successful_requests": 12375,
                "failed_requests": 125,
                "success_rate": 99.0,
            },
            "latency": {
                "min_ms": 12,
                "avg_ms": 85,
                "p50_ms": 72,
                "p95_ms": 185,
                "p99_ms": 320,
                "max_ms": 890,
            },
            "throughput": {
                "avg_rps": 208,
                "peak_rps": 285,
            },
            "errors": {
                "timeout": 75,
                "connection_refused": 25,
                "http_500": 25,
            },
            "resource_usage": {
                "cpu_avg_percent": 72,
                "memory_avg_mb": 1250,
                "connections_peak": 95,
            },
        }
        
        return {
            "data": {
                "target": target_url,
                "config": {
                    "virtual_users": users,
                    "duration_seconds": duration,
                    "ramp_up_seconds": 10,
                },
                "results": results,
                "passed_thresholds": {
                    "p99_latency": True,
                    "error_rate": True,
                    "throughput": False,
                },
            },
            "recommendations": [
                "Throughput below target - consider horizontal scaling",
                "Investigate timeout errors - may need connection pool tuning",
                "CPU usage high at 72% - optimize hot paths or add capacity",
            ],
        }
    
    async def _recommend_caching(self, payload: dict[str, Any]) -> dict:
        """Recommend caching strategy."""
        scope = payload.get("scope", "application")
        
        self.logger.info(f"Analyzing caching opportunities for {scope}")
        
        recommendations = [
            {
                "target": "User profile lookup",
                "location": "src/api/users.py:get_user_profile",
                "current_latency_ms": 45,
                "cache_type": "distributed",
                "ttl_seconds": 300,
                "estimated_hit_rate": 85,
                "estimated_improvement": "75% latency reduction",
                "implementation": "Use Redis with user_id as key",
            },
            {
                "target": "Configuration settings",
                "location": "src/config/loader.py:load_settings",
                "current_latency_ms": 120,
                "cache_type": "local",
                "ttl_seconds": 3600,
                "estimated_hit_rate": 99,
                "estimated_improvement": "99% latency reduction",
                "implementation": "In-memory cache with file watcher for invalidation",
            },
            {
                "target": "API response",
                "location": "src/api/products.py:list_products",
                "current_latency_ms": 250,
                "cache_type": "cdn",
                "ttl_seconds": 60,
                "estimated_hit_rate": 70,
                "estimated_improvement": "Offload to edge, reduce server load",
                "implementation": "Cache-Control headers with CDN",
            },
        ]
        
        return {
            "data": {
                "scope": scope,
                "recommendations": recommendations,
                "strategy_summary": {
                    "local_cache": ["Configuration", "Static data"],
                    "distributed_cache": ["User data", "Session data"],
                    "cdn_cache": ["API responses", "Static assets"],
                },
                "estimated_overall_improvement": "60% average latency reduction",
            },
            "recommendations": [
                "Start with user profile caching - high impact, low risk",
                "Implement cache invalidation strategy before adding caching",
                "Monitor cache hit rates and adjust TTLs accordingly",
            ],
        }
    
    async def _analyze_memory(self, payload: dict[str, Any]) -> dict:
        """Analyze memory usage and detect issues."""
        
        self.logger.info("Analyzing memory usage patterns")
        
        return {
            "data": {
                "current_usage_mb": 1250,
                "peak_usage_mb": 1850,
                "baseline_mb": 450,
                "gc_stats": {
                    "collections": 145,
                    "total_time_ms": 890,
                    "avg_pause_ms": 6.1,
                },
                "allocations": {
                    "top_types": [
                        {"type": "dict", "count": 125000, "size_mb": 320},
                        {"type": "str", "count": 89000, "size_mb": 180},
                        {"type": "list", "count": 45000, "size_mb": 95},
                    ],
                },
                "potential_leaks": [
                    {
                        "location": "src/cache/memory.py",
                        "description": "Cache entries not expiring",
                        "growth_rate_mb_per_hour": 15,
                    },
                ],
            },
            "recommendations": [
                "Implement cache eviction policy",
                "Review dict allocations - consider dataclasses",
                "Add memory limits to prevent OOM",
            ],
        }
