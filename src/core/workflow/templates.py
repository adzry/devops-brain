"""
Workflow Templates

Pre-built workflow templates for common DevOps scenarios.
"""

from .dag import DAG, Node, NodeType


def ci_pipeline_template() -> DAG:
    """CI Pipeline: Lint → Test → Build → Scan"""
    dag = DAG(name="CI Pipeline")
    
    # Nodes
    lint_id = dag.add_node(Node(
        name="Lint",
        type=NodeType.TASK,
        action="run_linter",
        agent="testing_agent",
    ))
    
    test_id = dag.add_node(Node(
        name="Test",
        type=NodeType.TASK,
        action="run_tests",
        agent="testing_agent",
    ))
    
    build_id = dag.add_node(Node(
        name="Build",
        type=NodeType.TASK,
        action="build_artifacts",
        agent="deployment_agent",
    ))
    
    scan_id = dag.add_node(Node(
        name="Security Scan",
        type=NodeType.TASK,
        action="scan_vulnerabilities",
        agent="security_agent",
    ))
    
    # Edges
    dag.add_edge(lint_id, test_id)
    dag.add_edge(test_id, build_id)
    dag.add_edge(build_id, scan_id)
    
    return dag


def deployment_pipeline_template() -> DAG:
    """Deployment Pipeline: Build → Test → Deploy → Verify"""
    dag = DAG(name="Deployment Pipeline")
    
    build_id = dag.add_node(Node(
        name="Build",
        type=NodeType.TASK,
        action="build_artifacts",
        agent="deployment_agent",
    ))
    
    test_id = dag.add_node(Node(
        name="Test",
        type=NodeType.TASK,
        action="run_tests",
        agent="testing_agent",
    ))
    
    deploy_id = dag.add_node(Node(
        name="Deploy",
        type=NodeType.TASK,
        action="deploy",
        agent="deployment_agent",
    ))
    
    verify_id = dag.add_node(Node(
        name="Verify",
        type=NodeType.TASK,
        action="health_check",
        agent="deployment_agent",
    ))
    
    dag.add_edge(build_id, test_id)
    dag.add_edge(test_id, deploy_id)
    dag.add_edge(deploy_id, verify_id)
    
    return dag


def security_scan_template() -> DAG:
    """Security Scan: Dependency Scan → Code Scan → Report"""
    dag = DAG(name="Security Scan")
    
    dep_scan_id = dag.add_node(Node(
        name="Dependency Scan",
        type=NodeType.TASK,
        action="scan_dependencies",
        agent="security_agent",
    ))
    
    code_scan_id = dag.add_node(Node(
        name="Code Scan",
        type=NodeType.TASK,
        action="scan_code",
        agent="security_agent",
    ))
    
    report_id = dag.add_node(Node(
        name="Generate Report",
        type=NodeType.TASK,
        action="generate_security_report",
        agent="security_agent",
    ))
    
    # Parallel scans
    dag.add_edge(dep_scan_id, report_id)
    dag.add_edge(code_scan_id, report_id)
    
    return dag


def database_migration_template() -> DAG:
    """Database Migration: Backup → Migrate → Verify → Notify"""
    dag = DAG(name="Database Migration")
    
    backup_id = dag.add_node(Node(
        name="Backup",
        type=NodeType.TASK,
        action="backup_database",
        agent="database_agent",
    ))
    
    migrate_id = dag.add_node(Node(
        name="Migrate",
        type=NodeType.TASK,
        action="run_migration",
        agent="database_agent",
    ))
    
    verify_id = dag.add_node(Node(
        name="Verify",
        type=NodeType.TASK,
        action="verify_migration",
        agent="database_agent",
    ))
    
    notify_id = dag.add_node(Node(
        name="Notify",
        type=NodeType.TASK,
        action="send_notification",
        agent="incident_response_agent",
    ))
    
    dag.add_edge(backup_id, migrate_id)
    dag.add_edge(migrate_id, verify_id)
    dag.add_edge(verify_id, notify_id)
    
    return dag


def incident_response_template() -> DAG:
    """Incident Response: Triage → Analyze → Remediate → Post-mortem"""
    dag = DAG(name="Incident Response")
    
    triage_id = dag.add_node(Node(
        name="Triage",
        type=NodeType.TASK,
        action="triage_incident",
        agent="incident_response_agent",
    ))
    
    analyze_id = dag.add_node(Node(
        name="Analyze",
        type=NodeType.TASK,
        action="root_cause_analysis",
        agent="incident_response_agent",
    ))
    
    remediate_id = dag.add_node(Node(
        name="Remediate",
        type=NodeType.TASK,
        action="remediate_incident",
        agent="incident_response_agent",
    ))
    
    postmortem_id = dag.add_node(Node(
        name="Post-mortem",
        type=NodeType.TASK,
        action="generate_postmortem",
        agent="incident_response_agent",
    ))
    
    dag.add_edge(triage_id, analyze_id)
    dag.add_edge(analyze_id, remediate_id)
    dag.add_edge(remediate_id, postmortem_id)
    
    return dag


# Template registry
TEMPLATES = {
    "ci_pipeline": ci_pipeline_template,
    "deployment_pipeline": deployment_pipeline_template,
    "security_scan": security_scan_template,
    "database_migration": database_migration_template,
    "incident_response": incident_response_template,
}


def get_template(name: str) -> DAG:
    """Get a workflow template by name."""
    template_fn = TEMPLATES.get(name)
    if not template_fn:
        raise ValueError(f"Template not found: {name}. Available: {list(TEMPLATES.keys())}")
    return template_fn()


def list_templates() -> list[dict]:
    """List all available templates."""
    return [
        {
            "name": name,
            "description": get_template(name).name,
        }
        for name in TEMPLATES.keys()
    ]
