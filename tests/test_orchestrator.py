from devops_brain.orchestrator import DevOpsBrain


def test_release_workflow_runs_successfully(tmp_path):
    brain = DevOpsBrain("configs/brain.yaml")
    result = brain.run_workflow("release", "Ship release")
    assert result.success is True
    assert "plan" in result.shared_state
