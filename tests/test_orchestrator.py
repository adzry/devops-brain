from devops_brain.orchestrator import DevOpsBrain


def test_loads_config_and_workflows():
    brain = DevOpsBrain()
    assert "root" in brain.config.agents
    assert len(brain.workflows) >= 1
