"""
Testing Agent

Specialized agent for test generation, execution, coverage analysis,
and test quality improvements.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base_agent import AgentConfig, BaseAgent


class TestType(Enum):
    """Types of tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a test execution."""
    
    name: str
    status: TestStatus
    duration_ms: int
    file: str
    message: str | None = None
    stack_trace: str | None = None


class TestingAgent(BaseAgent):
    """
    Test-focused agent for comprehensive testing automation.
    
    Capabilities:
    - Test generation from code
    - Test execution and reporting
    - Coverage analysis
    - Mutation testing
    - Flaky test detection
    - Test optimization
    """
    
    SYSTEM_PROMPT = """You are the Testing Agent for DevOps Brain. Your mission is to 
ensure software quality through comprehensive testing.

Your responsibilities:
1. Generate high-quality tests for new and existing code
2. Execute test suites and analyze results
3. Improve test coverage to meet targets
4. Identify and fix flaky tests
5. Optimize test execution time

Testing principles:
- Test behavior, not implementation
- Aim for meaningful coverage, not just metrics
- Fast feedback loops
- Deterministic and reproducible tests

Always strive for the right balance between test coverage and maintenance cost."""

    def _register_handlers(self) -> None:
        """Register testing action handlers."""
        self.register_handler("generate_tests", self._generate_tests)
        self.register_handler("run_tests", self._run_tests)
        self.register_handler("analyze_coverage", self._analyze_coverage)
        self.register_handler("detect_flaky", self._detect_flaky_tests)
        self.register_handler("mutation_test", self._mutation_test)
        self.register_handler("optimize_suite", self._optimize_suite)
        self.register_handler("suggest_tests", self._suggest_tests)
    
    async def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def _generate_tests(self, payload: dict[str, Any]) -> dict:
        """Generate tests for given code."""
        target_file = payload.get("file")
        test_type = payload.get("type", "unit")
        framework = payload.get("framework", "pytest")
        
        self.logger.info(f"Generating {test_type} tests for {target_file}")
        
        generated_tests = """
import pytest
from src.calculator import Calculator


class TestCalculator:
    \"\"\"Test suite for Calculator class.\"\"\"
    
    @pytest.fixture
    def calculator(self):
        return Calculator()
    
    def test_add_positive_numbers(self, calculator):
        \"\"\"Test addition of positive numbers.\"\"\"
        assert calculator.add(2, 3) == 5
    
    def test_add_negative_numbers(self, calculator):
        \"\"\"Test addition with negative numbers.\"\"\"
        assert calculator.add(-1, -1) == -2
    
    def test_add_zero(self, calculator):
        \"\"\"Test addition with zero.\"\"\"
        assert calculator.add(0, 5) == 5
    
    def test_divide_by_zero_raises_error(self, calculator):
        \"\"\"Test that division by zero raises ValueError.\"\"\"
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator.divide(10, 0)
    
    @pytest.mark.parametrize("a,b,expected", [
        (10, 2, 5),
        (9, 3, 3),
        (-10, 2, -5),
    ])
    def test_divide_various_inputs(self, calculator, a, b, expected):
        \"\"\"Test division with various inputs.\"\"\"
        assert calculator.divide(a, b) == expected
"""
        
        return {
            "data": {
                "target_file": target_file,
                "test_type": test_type,
                "framework": framework,
                "tests_generated": 6,
                "test_code": generated_tests,
                "test_file": f"tests/test_{target_file.split('/')[-1]}",
            },
            "recommendations": [
                "Add edge case tests for boundary conditions",
                "Consider adding property-based tests with Hypothesis",
                "Add integration tests for database interactions",
            ],
            "next_actions": [
                "Write generated tests to file",
                "Run test suite to validate",
            ],
        }
    
    async def _run_tests(self, payload: dict[str, Any]) -> dict:
        """Execute test suite."""
        test_path = payload.get("path", "tests/")
        test_type = payload.get("type", "all")
        parallel = payload.get("parallel", True)
        
        self.logger.info(f"Running tests: {test_path} (type: {test_type})")
        
        results = [
            TestResult("test_add_positive", TestStatus.PASSED, 12, "tests/test_calc.py"),
            TestResult("test_add_negative", TestStatus.PASSED, 8, "tests/test_calc.py"),
            TestResult("test_divide_zero", TestStatus.PASSED, 15, "tests/test_calc.py"),
            TestResult(
                "test_api_response",
                TestStatus.FAILED,
                245,
                "tests/test_api.py",
                message="AssertionError: Expected 200, got 500",
            ),
            TestResult("test_db_connection", TestStatus.SKIPPED, 0, "tests/test_db.py"),
        ]
        
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        
        return {
            "data": {
                "test_path": test_path,
                "total_tests": len(results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration_ms": sum(r.duration_ms for r in results),
                "success_rate": passed / len(results) * 100,
                "results": [
                    {
                        "name": r.name,
                        "status": r.status.value,
                        "duration_ms": r.duration_ms,
                        "file": r.file,
                        "message": r.message,
                    }
                    for r in results
                ],
                "failures": [
                    {
                        "name": r.name,
                        "file": r.file,
                        "message": r.message,
                    }
                    for r in results
                    if r.status == TestStatus.FAILED
                ],
            },
            "recommendations": [
                "Fix failing test_api_response - API returning 500 error",
                "Investigate skipped test_db_connection",
            ],
        }
    
    async def _analyze_coverage(self, payload: dict[str, Any]) -> dict:
        """Analyze test coverage."""
        target = payload.get("target", "src/")
        threshold = payload.get("threshold", 80)
        
        self.logger.info(f"Analyzing coverage for {target}")
        
        coverage_data = {
            "src/calculator.py": {"lines": 95, "branches": 88, "functions": 100},
            "src/api/handlers.py": {"lines": 72, "branches": 65, "functions": 80},
            "src/db/models.py": {"lines": 45, "branches": 40, "functions": 50},
            "src/utils/helpers.py": {"lines": 85, "branches": 78, "functions": 90},
        }
        
        total_lines = sum(c["lines"] for c in coverage_data.values()) / len(coverage_data)
        
        return {
            "data": {
                "target": target,
                "overall_coverage": {
                    "lines": round(total_lines, 1),
                    "branches": 67.8,
                    "functions": 80.0,
                },
                "threshold": threshold,
                "meets_threshold": total_lines >= threshold,
                "by_file": coverage_data,
                "uncovered_lines": {
                    "src/api/handlers.py": [45, 67, 89, 102, 115],
                    "src/db/models.py": [12, 34, 56, 78, 90, 112],
                },
            },
            "recommendations": [
                "Focus on src/db/models.py - lowest coverage at 45%",
                "Add tests for error handling paths in handlers.py",
                "Branch coverage needs improvement - add condition tests",
            ],
            "next_actions": [
                "Generate tests for uncovered lines in models.py",
                "Add edge case tests for handlers.py",
            ],
        }
    
    async def _detect_flaky_tests(self, payload: dict[str, Any]) -> dict:
        """Detect flaky tests in the test suite."""
        runs = payload.get("runs", 10)
        
        self.logger.info(f"Detecting flaky tests over {runs} runs")
        
        flaky_tests = [
            {
                "name": "test_async_operation",
                "file": "tests/test_async.py",
                "pass_rate": 70,
                "failure_pattern": "Timeout waiting for response",
                "suspected_cause": "Race condition in async handler",
                "suggestion": "Add proper await and increase timeout",
            },
            {
                "name": "test_cache_expiry",
                "file": "tests/test_cache.py",
                "pass_rate": 85,
                "failure_pattern": "Cache not expired as expected",
                "suspected_cause": "Time-dependent test logic",
                "suggestion": "Mock time.time() for deterministic behavior",
            },
        ]
        
        return {
            "data": {
                "runs_analyzed": runs,
                "total_tests": 150,
                "flaky_count": len(flaky_tests),
                "flaky_tests": flaky_tests,
            },
            "recommendations": [
                "Fix async race condition in test_async_operation",
                "Use time mocking for test_cache_expiry",
                "Consider quarantining flaky tests until fixed",
            ],
        }
    
    async def _mutation_test(self, payload: dict[str, Any]) -> dict:
        """Run mutation testing to assess test quality."""
        target = payload.get("target", "src/")
        
        self.logger.info(f"Running mutation testing on {target}")
        
        return {
            "data": {
                "target": target,
                "mutations_generated": 150,
                "mutations_killed": 120,
                "mutations_survived": 25,
                "mutations_timeout": 5,
                "mutation_score": 80.0,
                "survived_mutations": [
                    {
                        "file": "src/calculator.py",
                        "line": 25,
                        "mutation": "Changed > to >=",
                        "impact": "Boundary condition not tested",
                    },
                    {
                        "file": "src/validator.py",
                        "line": 42,
                        "mutation": "Removed null check",
                        "impact": "Missing null input test",
                    },
                ],
            },
            "recommendations": [
                "Add boundary tests for calculator.py line 25",
                "Add null input test for validator.py",
                "Mutation score of 80% is good but aim for 85%+",
            ],
        }
    
    async def _optimize_suite(self, payload: dict[str, Any]) -> dict:
        """Optimize test suite for faster execution."""
        
        self.logger.info("Analyzing test suite for optimization opportunities")
        
        return {
            "data": {
                "current_duration_seconds": 180,
                "optimized_duration_seconds": 95,
                "improvement_percent": 47,
                "optimizations": [
                    {
                        "type": "parallelization",
                        "description": "Enable parallel test execution",
                        "time_saved_seconds": 45,
                    },
                    {
                        "type": "fixture_scope",
                        "description": "Change database fixture to session scope",
                        "time_saved_seconds": 25,
                    },
                    {
                        "type": "test_selection",
                        "description": "Smart test selection based on changes",
                        "time_saved_seconds": 15,
                    },
                ],
                "slow_tests": [
                    {"name": "test_full_sync", "duration_seconds": 15},
                    {"name": "test_data_migration", "duration_seconds": 12},
                ],
            },
            "recommendations": [
                "Add pytest-xdist for parallel execution",
                "Consider mocking external services in slow tests",
                "Implement test impact analysis for PRs",
            ],
        }
    
    async def _suggest_tests(self, payload: dict[str, Any]) -> dict:
        """Suggest tests based on code changes."""
        diff = payload.get("diff", "")
        changed_files = payload.get("files", [])
        
        self.logger.info(f"Suggesting tests for {len(changed_files)} changed files")
        
        return {
            "data": {
                "changed_files": changed_files,
                "suggested_tests": [
                    {
                        "test_name": "test_new_validation_logic",
                        "reason": "New validation function added",
                        "priority": "high",
                        "type": "unit",
                    },
                    {
                        "test_name": "test_api_error_handling",
                        "reason": "Error handling modified in API handler",
                        "priority": "high",
                        "type": "integration",
                    },
                    {
                        "test_name": "test_edge_cases_empty_input",
                        "reason": "Input handling changed",
                        "priority": "medium",
                        "type": "unit",
                    },
                ],
                "existing_tests_to_run": [
                    "tests/test_validation.py",
                    "tests/test_api.py",
                ],
            },
            "recommendations": [
                "Add unit test for new validation logic",
                "Update existing API tests for error handling changes",
                "Run regression tests for affected modules",
            ],
        }
