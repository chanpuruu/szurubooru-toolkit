from types import SimpleNamespace

import click
import pytest
from click.testing import CliRunner

import szurubooru_toolkit
from szurubooru_toolkit.scripts import szuru_toolkit


def test_categorize_tags_rejects_conflicting_apply_modes():
    result = CliRunner().invoke(szuru_toolkit.cli, ['categorize-tags', '--apply', '--report-only'])

    assert result.exit_code == 2
    assert '--apply and --report-only cannot be used together' in result.output


def test_categorize_tags_rejects_two_report_paths(tmp_path):
    report = tmp_path / 'review.csv'
    report.write_text('placeholder', encoding='utf-8')

    result = CliRunner().invoke(
        szuru_toolkit.cli,
        ['categorize-tags', '--from-report', str(report), '--report-file', str(tmp_path / 'other.csv')],
    )

    assert result.exit_code == 2
    assert '--from-report and --report-file cannot be used together' in result.output


@pytest.mark.parametrize(('from_report', 'expected'), [('', True), ('review.csv', False)])
def test_setup_module_only_creates_rule34_for_source_scans(monkeypatch, from_report, expected):
    setup_calls = []
    fake_config = SimpleNamespace(override_config=lambda overrides: None)
    context = SimpleNamespace(obj={}, params={'from_report': from_report})

    monkeypatch.setattr(szurubooru_toolkit, 'config', fake_config)
    monkeypatch.setattr(szuru_toolkit, 'setup_config', lambda: None)
    monkeypatch.setattr(szuru_toolkit, 'setup_logger', lambda: None)
    monkeypatch.setattr(
        szuru_toolkit,
        'setup_clients',
        lambda include_rule34=False, include_sankaku=True: setup_calls.append((include_rule34, include_sankaku)),
    )
    monkeypatch.setattr(szuru_toolkit.importlib, 'import_module', lambda name: SimpleNamespace())

    szuru_toolkit.setup_module('categorize_tags', context)

    assert setup_calls == [(expected, False)]


def test_setup_module_turns_rule34_config_error_into_usage_error(monkeypatch):
    fake_config = SimpleNamespace(override_config=lambda overrides: None)
    context = SimpleNamespace(obj={}, params={'from_report': ''})

    monkeypatch.setattr(szurubooru_toolkit, 'config', fake_config)
    monkeypatch.setattr(szuru_toolkit, 'setup_config', lambda: None)
    monkeypatch.setattr(szuru_toolkit, 'setup_logger', lambda: None)
    monkeypatch.setattr(
        szuru_toolkit,
        'setup_clients',
        lambda include_rule34=False, include_sankaku=True: (_ for _ in ()).throw(ValueError('invalid Rule34 settings')),
    )

    with pytest.raises(click.UsageError, match='invalid Rule34 settings'):
        szuru_toolkit.setup_module('categorize_tags', context)
