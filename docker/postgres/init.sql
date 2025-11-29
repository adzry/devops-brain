-- DevOps Brain Database Initialization
-- Creates necessary tables and indexes

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(255) NOT NULL,
    payload JSONB DEFAULT '{}',
    target_agent VARCHAR(100),
    priority INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_agent ON tasks(target_agent);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'inactive',
    capabilities TEXT[],
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agents_name ON agents(name);
CREATE INDEX idx_agents_status ON agents(status);

-- Workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow runs table
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflows(id),
    status VARCHAR(50) DEFAULT 'pending',
    trigger_type VARCHAR(50),
    trigger_data JSONB,
    results JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workflow_runs_workflow ON workflow_runs(workflow_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    actor VARCHAR(100),
    changes JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Insert default agents
INSERT INTO agents (name, type, status, capabilities) VALUES
    ('security_agent', 'specialist', 'active', ARRAY['vulnerability_scanning', 'secrets_detection', 'compliance_checking']),
    ('testing_agent', 'specialist', 'active', ARRAY['test_generation', 'test_execution', 'coverage_analysis']),
    ('documentation_agent', 'specialist', 'active', ARRAY['api_documentation', 'readme_generation', 'changelog_management']),
    ('performance_agent', 'specialist', 'active', ARRAY['performance_profiling', 'bottleneck_detection', 'load_testing']),
    ('incident_response_agent', 'specialist', 'active', ARRAY['incident_triage', 'root_cause_analysis', 'runbook_execution']),
    ('database_agent', 'specialist', 'active', ARRAY['schema_design', 'migration_generation', 'query_optimization']),
    ('infrastructure_agent', 'specialist', 'active', ARRAY['terraform_management', 'kubernetes_orchestration', 'cost_optimization'])
ON CONFLICT (name) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO devops;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO devops;
