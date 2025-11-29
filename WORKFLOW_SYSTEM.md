# Enhanced Workflow System

## Overview

DevOps Brain now includes a **powerful, enterprise-grade workflow system** that rivals N8n but is specifically optimized for DevOps automation. Instead of integrating N8n (which would add external dependencies), we built a better solution that:

- ✅ **Fully integrated** with DevOps Brain agents
- ✅ **No external dependencies** - self-contained
- ✅ **Optimized for DevOps** use cases
- ✅ **Better performance** - native Python async
- ✅ **Full control** - customize as needed

## Features

### 1. **DAG-Based Workflows**
- Visual workflow definition
- Parallel execution
- Conditional branching
- Dependency management
- Cycle detection

### 2. **Scheduled Workflows** (Cron)
- Cron-based scheduling
- One-time scheduled execution
- Timezone support
- Automatic execution

### 3. **Webhook Triggers**
- HTTP webhook endpoints
- Secret validation (HMAC)
- Request filtering
- Webhook history

### 4. **Workflow Persistence**
- Database storage
- Version management
- Metadata and tags
- Execution history

### 5. **REST API**
- Full CRUD operations
- Workflow execution
- Schedule management
- Webhook registration

## Quick Start

### Create a Workflow

```python
from src.core.workflow import WorkflowEngine, WorkflowBuilder

engine = WorkflowEngine(orchestrator=orchestrator)
await engine.initialize()

# Using builder pattern
workflow = engine.create_workflow("CI Pipeline")
    .add_task("lint", "run_linter", agent="testing_agent")
    .add_task("test", "run_tests", agent="testing_agent")
    .add_task("scan", "scan_vulnerabilities", agent="security_agent")
    .connect("lint", "test")
    .connect("test", "scan")
    .register()

# Or from definition
workflow_dict = {
    "name": "Deploy Pipeline",
    "nodes": [
        {"id": "1", "name": "build", "type": "task", "action": "build"},
        {"id": "2", "name": "deploy", "type": "task", "action": "deploy"},
    ],
    "edges": [{"source": "1", "target": "2"}],
}
dag = DAG.from_dict(workflow_dict)
workflow_id = engine.register(dag)
```

### Schedule a Workflow

```python
# Schedule to run daily at 2 AM
schedule_id = engine.scheduler.schedule(
    workflow_id="my-workflow",
    cron_expression="0 2 * * *",
    context={"environment": "production"},
)

# Schedule one-time execution
schedule_id = engine.scheduler.schedule_once(
    workflow_id="my-workflow",
    run_at=datetime(2024, 12, 25, 10, 0),
)
```

### Register a Webhook

```python
webhook_id = engine.webhooks.register(
    workflow_id="deploy-workflow",
    path="/webhook/deploy",
    method="POST",
    secret="my-secret-key",
    filters={"header.X-Event": "deployment"},
)
```

### Execute a Workflow

```python
# Direct execution
result = await engine.run(workflow_id, context={"branch": "main"})

# Via webhook
result = await engine.webhooks.trigger(webhook_id, {"branch": "main"})
```

## API Endpoints

### Workflow Management

```bash
# Create workflow
POST /api/v1/workflows
{
  "name": "CI Pipeline",
  "nodes": [...],
  "edges": [...]
}

# List workflows
GET /api/v1/workflows?tags=ci,deploy&search=pipeline

# Get workflow
GET /api/v1/workflows/{workflow_id}

# Delete workflow
DELETE /api/v1/workflows/{workflow_id}
```

### Execution

```bash
# Run workflow
POST /api/v1/workflows/{workflow_id}/run
{
  "context": {"branch": "main"}
}

# List executions
GET /api/v1/workflows/{workflow_id}/runs?limit=50
```

### Scheduling

```bash
# Schedule workflow
POST /api/v1/workflows/{workflow_id}/schedule
{
  "cron_expression": "0 2 * * *",
  "context": {},
  "enabled": true
}

# List schedules
GET /api/v1/workflows/{workflow_id}/schedules

# Remove schedule
DELETE /api/v1/schedules/{schedule_id}
```

### Webhooks

```bash
# Register webhook
POST /api/v1/workflows/{workflow_id}/webhooks
{
  "path": "/webhook/deploy",
  "method": "POST",
  "secret": "optional-secret"
}

# Trigger webhook
POST /api/v1/webhooks/{webhook_id}/trigger
{
  "branch": "main",
  "environment": "production"
}

# List webhooks
GET /api/v1/workflows/{workflow_id}/webhooks
```

## Workflow Node Types

### Task Node
Executes an agent action:
```python
.add_task("scan", "scan_vulnerabilities", agent="security_agent")
```

### Condition Node
Conditional branching:
```python
.add_condition("check", "ctx.scan_result.vulnerabilities == 0")
```

### Wait Node
Delay execution:
```python
.add_wait("delay", seconds=60)
```

### Transform Node
Data transformation:
```python
.add_transform("format", transform_fn=lambda ctx: {...})
```

## Advanced Features

### Context Interpolation

Use `${node_id.field}` to reference previous node results:

```python
.add_task("scan", "scan_vulnerabilities")
.add_task("report", "generate_report", payload={
    "vulnerabilities": "${scan.result.vulnerabilities}"
})
```

### Error Handling

```python
.add_task(
    "risky_task",
    "some_action",
    continue_on_failure=True,  # Continue even if fails
    retry_count=3,              # Retry 3 times
    retry_delay=5,              # Wait 5s between retries
)
```

### Parallel Execution

```python
workflow = engine.create_workflow("Parallel Tests")
    .add_task("test_unit", "run_unit_tests")
    .add_task("test_integration", "run_integration_tests")
    .add_task("test_e2e", "run_e2e_tests")
    # All three run in parallel (no connections)
    .register()
```

## Comparison with N8n

| Feature | DevOps Brain | N8n |
|---------|--------------|-----|
| **Integration** | Native agent integration | External API calls |
| **Performance** | Async Python, optimized | Node.js, HTTP overhead |
| **Dependencies** | Self-contained | External service |
| **Customization** | Full source control | Limited |
| **DevOps Focus** | Built for DevOps | General purpose |
| **Cost** | Free (self-hosted) | Free tier limited |
| **Visual Builder** | Coming soon | ✅ Yes |
| **Templates** | ✅ Yes | ✅ Yes |
| **Webhooks** | ✅ Yes | ✅ Yes |
| **Scheduling** | ✅ Yes | ✅ Yes |

## Workflow Templates

Pre-built templates available:

1. **CI Pipeline** - Lint → Test → Build → Scan
2. **Deployment** - Build → Test → Deploy → Verify
3. **Security Scan** - Dependency scan → Code scan → Report
4. **Database Migration** - Backup → Migrate → Verify → Notify
5. **Incident Response** - Triage → Analyze → Remediate → Post-mortem

## Best Practices

1. **Use descriptive names** for workflows and nodes
2. **Add metadata** (tags, description) for organization
3. **Test workflows** with small datasets first
4. **Use webhooks** for event-driven automation
5. **Schedule regular workflows** (backups, scans)
6. **Monitor execution history** for failures
7. **Use conditions** for smart branching
8. **Leverage parallel execution** for speed

## Migration from N8n

If you're using N8n, migration is straightforward:

1. Export N8n workflows (JSON)
2. Convert to DevOps Brain format (similar structure)
3. Import via API or builder
4. Test and validate
5. Switch triggers (webhooks/schedules)

## Future Enhancements

- [ ] Visual workflow builder UI
- [ ] Workflow marketplace
- [ ] Workflow versioning
- [ ] A/B testing workflows
- [ ] Workflow analytics dashboard
- [ ] Workflow sharing/collaboration
- [ ] Workflow debugging tools

## Examples

See `workflows/` directory for example workflow definitions:
- `ci_workflow.yaml` - Continuous integration
- `deploy_workflow.yaml` - Deployment pipeline
- `pr_workflow.yaml` - Pull request automation
