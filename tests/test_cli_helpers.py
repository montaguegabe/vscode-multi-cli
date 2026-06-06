import click
from click.testing import CliRunner

from multi.cli_helpers import common_command_wrapper


class FakeSettings:
    def is_monorepo(self):
        return False


class FakePaths:
    settings = FakeSettings()

    def __init__(self, root_dir, install_set=None):
        self.root_dir = root_dir
        self.install_set = install_set


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


def test_common_command_wrapper_runs_branch_check_after_success(monkeypatch):
    @click.command(name="ok")
    def ok_cmd():
        click.echo("done")
        return "result"

    branch_checks = []

    def fake_check_all_on_same_branch(*, paths, raise_error):
        branch_checks.append((paths, raise_error))
        return True

    monkeypatch.setattr("multi.cli_helpers.Paths", FakePaths)
    monkeypatch.setattr(
        "multi.cli_helpers.check_all_on_same_branch", fake_check_all_on_same_branch
    )

    result = CliRunner().invoke(common_command_wrapper(ok_cmd))

    assert result.exit_code == 0
    assert "done" in result.output
    assert len(branch_checks) == 1
    assert isinstance(branch_checks[0][0], FakePaths)
    assert branch_checks[0][1] is True


def test_common_command_wrapper_skips_parent_group_check_before_subcommand(
    monkeypatch,
):
    @click.group(name="parent", invoke_without_command=True)
    def parent_cmd():
        pass

    @click.command(name="child")
    def child_cmd():
        click.echo("child")

    parent_cmd.add_command(child_cmd)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("parent branch check should not run before child command")

    monkeypatch.setattr("multi.cli_helpers.Paths", fail_if_called)
    monkeypatch.setattr("multi.cli_helpers.check_all_on_same_branch", fail_if_called)

    result = CliRunner().invoke(common_command_wrapper(parent_cmd), ["child"])

    assert result.exit_code == 0
    assert "child" in result.output
