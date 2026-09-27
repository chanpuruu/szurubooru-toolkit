import importlib.util

from click.testing import CliRunner

from szurubooru_toolkit.scripts import szuru_toolkit


def test_legacy_bridge_removed_without_initializing_toolkit(monkeypatch):
    def forbidden_setup(*args, **kwargs):
        raise AssertionError('Help and retired commands must not initialize the toolkit')

    monkeypatch.setattr(szuru_toolkit, 'setup_config', forbidden_setup)
    monkeypatch.setattr(szuru_toolkit, 'setup_clients', forbidden_setup)
    runner = CliRunner()

    result = runner.invoke(szuru_toolkit.cli, ['webserver'])
    assert result.exit_code == 2
    assert "No such command 'webserver'" in result.output
    assert 'webserver' not in szuru_toolkit.cli.commands
    assert importlib.util.find_spec('szurubooru_toolkit.scripts.webserver') is None

    help_result = runner.invoke(szuru_toolkit.cli, ['--help'])
    assert help_result.exit_code == 0
    assert 'webserver' not in help_result.output
    assert 'import-from-url' in help_result.output
    assert runner.invoke(szuru_toolkit.cli, ['import-from-url', '--help']).exit_code == 0
