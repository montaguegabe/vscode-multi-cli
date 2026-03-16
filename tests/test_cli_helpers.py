import click
from click.testing import CliRunner

from multi.cli_helpers import common_command_wrapper


def test_common_command_wrapper_skips_branch_checks_after_failure(monkeypatch):
    @click.command(name="failing")
    def failing_cmd():
        raise RuntimeError("boom")

    wrapped_cmd = common_command_wrapper(failing_cmd)
    runner = CliRunner()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("branch checks should not run after command failure")

    monkeypatch.setattr("multi.cli_helpers.Paths", fail_if_called)
    monkeypatch.setattr("multi.cli_helpers.check_all_on_same_branch", fail_if_called)

    result = runner.invoke(wrapped_cmd)

    assert result.exit_code == 1
    assert "boom" in result.output
