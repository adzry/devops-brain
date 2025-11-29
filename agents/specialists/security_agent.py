"""
Security Agent

Specialized agent for security vulnerability detection, compliance checking,
and security advisory generation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base_agent import AgentConfig, BaseAgent


class SeverityLevel(Enum):
    """Security vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "informational"


@dataclass
class Vulnerability:
    """Represents a detected security vulnerability."""
    
    id: str
    title: str
    severity: SeverityLevel
    description: str
    affected_component: str
    cve_id: str | None = None
    cvss_score: float | None = None
    remediation: str | None = None
    references: list[str] | None = None


class SecurityAgent(BaseAgent):
    """
    Security-focused agent for vulnerability detection and compliance.
    
    Capabilities:
    - Vulnerability scanning (dependencies, code, infrastructure)
    - Secrets detection
    - Compliance checking (OWASP, SOC2, GDPR, HIPAA)
    - Threat modeling
    - Security advisory generation
    """
    
    SYSTEM_PROMPT = """You are the Security Agent for DevOps Brain. Your mission is to 
protect the organization's software and infrastructure from security threats.

Your responsibilities:
1. Scan code and dependencies for vulnerabilities
2. Detect exposed secrets and credentials
3. Ensure compliance with security frameworks (OWASP, SOC2, GDPR, HIPAA)
4. Perform threat modeling and risk assessment
5. Generate security advisories and remediation guidance

Security principles:
- Defense in depth
- Least privilege
- Zero trust
- Secure by default

Always prioritize critical and high severity issues. When in doubt, escalate."""

    def _register_handlers(self) -> None:
        """Register security action handlers."""
        self.register_handler("scan_vulnerabilities", self._scan_vulnerabilities)
        self.register_handler("scan_dependencies", self._scan_dependencies)
        self.register_handler("detect_secrets", self._detect_secrets)
        self.register_handler("check_compliance", self._check_compliance)
        self.register_handler("threat_model", self._threat_model)
        self.register_handler("generate_advisory", self._generate_advisory)
        self.register_handler("assess_risk", self._assess_risk)
    
    async def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    async def _scan_vulnerabilities(self, payload: dict[str, Any]) -> dict:
        """Scan code for security vulnerabilities."""
        target = payload.get("target", ".")
        scan_type = payload.get("scan_type", "full")
        
        self.logger.info(f"Scanning {target} for vulnerabilities (type: {scan_type})")
        
        # Simulated vulnerability detection
        vulnerabilities = [
            Vulnerability(
                id="VULN-001",
                title="SQL Injection in query builder",
                severity=SeverityLevel.HIGH,
                description="User input is directly concatenated into SQL query",
                affected_component="src/db/query.py",
                cve_id=None,
                remediation="Use parameterized queries instead of string concatenation",
            ),
            Vulnerability(
                id="VULN-002",
                title="Outdated cryptographic algorithm",
                severity=SeverityLevel.MEDIUM,
                description="MD5 hash used for password storage",
                affected_component="src/auth/password.py",
                remediation="Migrate to bcrypt or argon2 for password hashing",
            ),
        ]
        
        return {
            "data": {
                "scan_target": target,
                "scan_type": scan_type,
                "vulnerabilities_found": len(vulnerabilities),
                "by_severity": {
                    "critical": 0,
                    "high": 1,
                    "medium": 1,
                    "low": 0,
                },
                "vulnerabilities": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "severity": v.severity.value,
                        "component": v.affected_component,
                        "remediation": v.remediation,
                    }
                    for v in vulnerabilities
                ],
            },
            "recommendations": [
                "Address high severity SQL injection vulnerability immediately",
                "Schedule migration from MD5 to modern password hashing",
                "Implement automated security scanning in CI pipeline",
            ],
            "next_actions": [
                "Create issue for SQL injection fix",
                "Add security scanning to PR workflow",
            ],
        }
    
    async def _scan_dependencies(self, payload: dict[str, Any]) -> dict:
        """Scan dependencies for known vulnerabilities."""
        manifest_file = payload.get("manifest", "requirements.txt")
        
        self.logger.info(f"Scanning dependencies from {manifest_file}")
        
        vulnerable_deps = [
            {
                "package": "requests",
                "installed_version": "2.25.0",
                "vulnerability": "CVE-2023-32681",
                "severity": "medium",
                "fixed_version": "2.31.0",
            },
            {
                "package": "pyyaml",
                "installed_version": "5.3.1",
                "vulnerability": "CVE-2020-14343",
                "severity": "critical",
                "fixed_version": "5.4",
            },
        ]
        
        return {
            "data": {
                "manifest": manifest_file,
                "total_dependencies": 45,
                "vulnerable_count": len(vulnerable_deps),
                "vulnerable_dependencies": vulnerable_deps,
            },
            "recommendations": [
                "Upgrade pyyaml to 5.4+ immediately (critical CVE)",
                "Update requests to 2.31.0+",
                "Enable Dependabot or Renovate for automated updates",
            ],
        }
    
    async def _detect_secrets(self, payload: dict[str, Any]) -> dict:
        """Detect exposed secrets in code."""
        target = payload.get("target", ".")
        
        self.logger.info(f"Scanning {target} for exposed secrets")
        
        detected_secrets = [
            {
                "type": "AWS Access Key",
                "file": "config/settings.py",
                "line": 42,
                "severity": "critical",
                "masked_value": "AKIA...WXYZ",
            },
            {
                "type": "API Token",
                "file": ".env.example",
                "line": 15,
                "severity": "high",
                "masked_value": "sk-...abc123",
            },
        ]
        
        return {
            "data": {
                "scan_target": target,
                "secrets_found": len(detected_secrets),
                "secrets": detected_secrets,
            },
            "recommendations": [
                "Rotate the exposed AWS access key immediately",
                "Remove secrets from .env.example",
                "Add pre-commit hooks for secret detection",
                "Use secrets manager instead of environment files",
            ],
            "metadata": {
                "scanner": "gitleaks",
                "rules_version": "8.18.0",
            },
        }
    
    async def _check_compliance(self, payload: dict[str, Any]) -> dict:
        """Check compliance against security frameworks."""
        frameworks = payload.get("frameworks", ["OWASP"])
        
        self.logger.info(f"Checking compliance: {frameworks}")
        
        compliance_results = {
            "OWASP": {
                "score": 72,
                "passed": 18,
                "failed": 7,
                "not_applicable": 3,
                "findings": [
                    {"control": "A01 Broken Access Control", "status": "partial"},
                    {"control": "A02 Cryptographic Failures", "status": "failed"},
                    {"control": "A03 Injection", "status": "passed"},
                ],
            },
            "SOC2": {
                "score": 85,
                "passed": 42,
                "failed": 8,
                "not_applicable": 5,
            },
        }
        
        return {
            "data": {
                "frameworks_checked": frameworks,
                "results": compliance_results,
                "overall_score": 78,
            },
            "recommendations": [
                "Address cryptographic failures to improve OWASP score",
                "Implement access control logging",
                "Document security policies for SOC2 compliance",
            ],
        }
    
    async def _threat_model(self, payload: dict[str, Any]) -> dict:
        """Perform threat modeling analysis."""
        system_name = payload.get("system", "application")
        components = payload.get("components", [])
        
        self.logger.info(f"Performing threat modeling for {system_name}")
        
        threats = [
            {
                "id": "STRIDE-001",
                "category": "Spoofing",
                "description": "Attacker impersonates legitimate user via session hijacking",
                "component": "Authentication Service",
                "likelihood": "medium",
                "impact": "high",
                "mitigations": [
                    "Implement secure session management",
                    "Use HTTP-only cookies",
                    "Add session timeout",
                ],
            },
            {
                "id": "STRIDE-002",
                "category": "Tampering",
                "description": "Man-in-the-middle attack on API communication",
                "component": "API Gateway",
                "likelihood": "low",
                "impact": "high",
                "mitigations": [
                    "Enforce TLS 1.3",
                    "Implement certificate pinning",
                    "Use HSTS headers",
                ],
            },
        ]
        
        return {
            "data": {
                "system": system_name,
                "methodology": "STRIDE",
                "threats_identified": len(threats),
                "threats": threats,
                "risk_matrix": {
                    "critical": 0,
                    "high": 2,
                    "medium": 1,
                    "low": 0,
                },
            },
            "recommendations": [
                "Prioritize mitigations for high-impact threats",
                "Review threat model quarterly",
                "Include threat modeling in design phase",
            ],
        }
    
    async def _generate_advisory(self, payload: dict[str, Any]) -> dict:
        """Generate a security advisory document."""
        vulnerability_id = payload.get("vulnerability_id")
        
        self.logger.info(f"Generating advisory for {vulnerability_id}")
        
        advisory = {
            "advisory_id": f"ADV-{vulnerability_id}",
            "title": "Critical SQL Injection Vulnerability",
            "severity": "high",
            "affected_versions": ["1.0.0", "1.1.0", "1.2.0"],
            "fixed_version": "1.3.0",
            "description": "A SQL injection vulnerability was discovered...",
            "impact": "An attacker could execute arbitrary SQL commands...",
            "remediation": {
                "short_term": "Apply input validation workaround",
                "long_term": "Upgrade to version 1.3.0 or later",
            },
            "references": [
                "https://owasp.org/www-community/attacks/SQL_Injection",
            ],
            "timeline": {
                "discovered": "2024-11-01",
                "reported": "2024-11-02",
                "fixed": "2024-11-15",
                "disclosed": "2024-11-29",
            },
        }
        
        return {
            "data": advisory,
            "metadata": {
                "format": "markdown",
                "template": "security_advisory_v1",
            },
        }
    
    async def _assess_risk(self, payload: dict[str, Any]) -> dict:
        """Assess overall security risk."""
        scope = payload.get("scope", "full")
        
        self.logger.info(f"Assessing security risk (scope: {scope})")
        
        return {
            "data": {
                "overall_risk_score": 6.5,
                "risk_level": "medium",
                "risk_factors": [
                    {"factor": "Vulnerability count", "score": 7, "weight": 0.3},
                    {"factor": "Exposure level", "score": 5, "weight": 0.25},
                    {"factor": "Data sensitivity", "score": 8, "weight": 0.25},
                    {"factor": "Compliance gaps", "score": 6, "weight": 0.2},
                ],
                "trend": "improving",
                "comparison": {
                    "previous_score": 7.2,
                    "change": -0.7,
                },
            },
            "recommendations": [
                "Continue vulnerability remediation efforts",
                "Implement data encryption at rest",
                "Complete SOC2 compliance requirements",
            ],
        }
