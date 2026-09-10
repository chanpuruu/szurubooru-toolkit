from types import SimpleNamespace

import click

import szurubooru_toolkit
from szurubooru_toolkit.rule34 import Rule34ResponseError
from szurubooru_toolkit.rule34 import Rule34TagResult
from szurubooru_toolkit.scripts import categorize_tags
from szurubooru_toolkit.scripts.categorize_tags import CATEGORY_COLORS
from szurubooru_toolkit.scripts.categorize_tags import ReviewRecord
from szurubooru_toolkit.scripts.categorize_tags import apply_records
from szurubooru_toolkit.scripts.categorize_tags import read_report
from szurubooru_toolkit.scripts.categorize_tags import resolve_tags
from szurubooru_toolkit.scripts.categorize_tags import should_apply
from szurubooru_toolkit.scripts.categorize_tags import write_report
from szurubooru_toolkit.szurubooru import Tag
from szurubooru_toolkit.szurubooru import TagCategory


class StubRule34:
    def __init__(self, results=None):
        self.results = results or {}
        self.calls = []

    def lookup(self, name):
        self.calls.append(name)
        result = self.results.get(name)
        if isinstance(result, Exception):
            raise result
        return result


class StubDanbooru:
    def __init__(self, categories=None, error=None):
        self.categories = categories or {}
        self.error = error
        self.calls = []

    def get_tag_categories(self, names, strict=False):
        self.calls.append((names, strict))
        if self.error:
            raise self.error
        return {name: self.categories[name] for name in names if name in self.categories}


def rule34_result(name, category, raw_type, mode='api', ambiguous=False):
    return Rule34TagResult(name, raw_type, category, 10, ambiguous, mode)


def test_rule34_takes_precedence_without_danbooru_call():
    tags = [Tag(['atdan'], usages=4)]
    rule34 = StubRule34({'atdan': rule34_result('atdan', 'artist', 'Artist')})
    danbooru = StubDanbooru({'atdan': 0})

    records = resolve_tags(tags, rule34, danbooru, workers=1, hide_progress=True)

    assert records[0].status == 'planned_change'
    assert records[0].proposed_category == 'artist'
    assert records[0].source == 'rule34'
    assert danbooru.calls == []


def test_rule34_ambiguity_is_preserved_in_report():
    tags = [Tag(['ambiguous_tag'], usages=4)]
    rule34 = StubRule34({'ambiguous_tag': rule34_result('ambiguous_tag', 'default', 'tag', ambiguous=True)})

    record = resolve_tags(tags, rule34, StubDanbooru(), workers=1, hide_progress=True)[0]

    assert record.status == 'resolved_unchanged'
    assert record.ambiguous is True


def test_danbooru_fallback_is_batched_and_uses_aliases():
    tags = [Tag(['local_name', 'danbooru_name'], usages=3), Tag(['general_tag'], usages=8)]
    rule34 = StubRule34()
    danbooru = StubDanbooru({'danbooru_name': 4, 'general_tag': 0})

    records = resolve_tags(tags, rule34, danbooru, workers=1, hide_progress=True)
    by_tag = {record.tag: record for record in records}

    assert len(danbooru.calls) == 1
    assert danbooru.calls[0][1] is True
    assert by_tag['local_name'].matched_name == 'danbooru_name'
    assert by_tag['local_name'].proposed_category == 'character'
    assert by_tag['general_tag'].status == 'resolved_unchanged'


def test_lookup_error_is_not_reported_as_not_found():
    tags = [Tag(['source_failed'], usages=2)]
    rule34 = StubRule34({'source_failed': Rule34ResponseError('bad response')})
    danbooru = StubDanbooru()

    record = resolve_tags(tags, rule34, danbooru, workers=1, hide_progress=True)[0]

    assert record.status == 'lookup_error'
    assert 'bad response' in record.detail


def test_report_round_trip_and_sorting(tmp_path):
    records = [
        ReviewRecord(tag='resolved', usages=100, proposed_category='default', status='resolved_unchanged'),
        ReviewRecord(tag='missing', usages=2, status='not_found'),
    ]
    report = tmp_path / 'review.csv'

    write_report(records, report)
    loaded = read_report(report)

    assert [record.tag for record in loaded] == ['missing', 'resolved']
    assert loaded[1].usages == 100
    assert loaded[1].ambiguous is False


class StubSzuru:
    def __init__(self):
        self.categories = [TagCategory('default', '#000000', 1, default=True)]
        self.tags = {
            'artist_tag': Tag(['artist_tag'], category='default', version=3),
            'already_changed': Tag(['already_changed'], category='character', version=4),
        }
        self.created = []
        self.updated = []
        self.category_error = None
        self.category_list_error = None

    def get_tag_categories(self):
        if self.category_list_error:
            raise self.category_list_error
        return self.categories

    def get_tags(self, query):
        assert query == 'category:default sort:usages'
        return list(self.tags.values())

    def create_tag_category(self, name, color, order):
        if self.category_error:
            raise self.category_error
        self.created.append((name, color, order))
        category = TagCategory(name, color, order)
        self.categories.append(category)
        return category

    def get_tag(self, name):
        return self.tags[name]

    def update_tag_category(self, name, version, category):
        self.updated.append((name, version, category))
        return Tag([name], category=category, version=version + 1)


def test_apply_creates_categories_then_updates_only_default_tags():
    records = [
        ReviewRecord(tag='artist_tag', proposed_category='artist', status='planned_change'),
        ReviewRecord(tag='already_changed', proposed_category='character', status='planned_change'),
    ]
    szuru = StubSzuru()

    apply_records(records, szuru)

    assert szuru.created == [('artist', '#c00000', 2), ('character', '#00aa00', 3)]
    assert szuru.updated == [('artist_tag', 3, 'artist')]
    assert records[0].status == 'applied'
    assert records[1].status == 'skipped_changed'


def test_category_creation_failure_aborts_all_tag_updates():
    records = [ReviewRecord(tag='artist_tag', proposed_category='artist', status='planned_change')]
    szuru = StubSzuru()
    szuru.category_error = RuntimeError('permission denied')

    apply_records(records, szuru, CATEGORY_COLORS)

    assert szuru.updated == []
    assert records[0].status == 'apply_failed'
    assert 'Category setup failed' in records[0].detail


def test_category_list_failure_aborts_all_tag_updates():
    records = [ReviewRecord(tag='artist_tag', proposed_category='artist', status='planned_change')]
    szuru = StubSzuru()
    szuru.category_list_error = RuntimeError('categories unavailable')

    apply_records(records, szuru)

    assert szuru.created == []
    assert szuru.updated == []
    assert records[0].status == 'apply_failed'
    assert 'categories unavailable' in records[0].detail


def test_saved_report_retries_previous_apply_failures():
    records = [
        ReviewRecord(
            tag='artist_tag',
            proposed_category='artist',
            status='apply_failed',
            detail='temporary failure',
        )
    ]
    szuru = StubSzuru()

    apply_records(records, szuru)

    assert szuru.updated == [('artist_tag', 3, 'artist')]
    assert records[0].status == 'applied'
    assert records[0].detail == ''


def test_read_report_rejects_non_actionable_planned_change(tmp_path):
    report = tmp_path / 'review.csv'
    write_report([ReviewRecord(tag='bad', status='planned_change')], report)

    try:
        read_report(report)
    except ValueError as error:
        assert 'no actionable category' in str(error)
    else:
        raise AssertionError('Invalid report was accepted')


def test_should_apply_defaults_to_report_only_without_tty():
    assert should_apply(False, False, interactive=False) is False
    assert should_apply(True, False, interactive=False) is True
    assert should_apply(False, True, interactive=True) is False


def make_settings(report_file):
    return SimpleNamespace(
        categorize_tags={
            'report_file': str(report_file),
            'workers': 1,
            'hide_progress': True,
            'category_colors': CATEGORY_COLORS,
        },
        globals={},
    )


def test_main_report_only_writes_csv_without_mutations(tmp_path, monkeypatch):
    report = tmp_path / 'review.csv'
    szuru = StubSzuru()
    rule34 = StubRule34({
        'artist_tag': rule34_result('artist_tag', 'artist', 'artist'),
        'already_changed': rule34_result('already_changed', 'character', 'character'),
    })

    monkeypatch.setattr(categorize_tags, 'config', make_settings(report))
    monkeypatch.setattr(szurubooru_toolkit, 'szuru', szuru, raising=False)
    monkeypatch.setattr(szurubooru_toolkit, 'rule34', rule34, raising=False)
    monkeypatch.setattr(szurubooru_toolkit, 'danbooru', StubDanbooru(), raising=False)

    categorize_tags.main(report_only=True)

    assert report.exists()
    assert szuru.created == []
    assert szuru.updated == []


def test_main_from_report_applies_without_source_clients(tmp_path, monkeypatch):
    report = tmp_path / 'review.csv'
    write_report(
        [ReviewRecord(tag='artist_tag', proposed_category='artist', source='rule34', status='planned_change')],
        report,
    )
    szuru = StubSzuru()

    monkeypatch.setattr(categorize_tags, 'config', make_settings(report))
    monkeypatch.setattr(szurubooru_toolkit, 'szuru', szuru, raising=False)
    monkeypatch.delattr(szurubooru_toolkit, 'rule34', raising=False)
    monkeypatch.delattr(szurubooru_toolkit, 'danbooru', raising=False)

    categorize_tags.main(apply=True, from_report=str(report))

    assert szuru.updated == [('artist_tag', 3, 'artist')]
    assert read_report(report)[0].status == 'applied'


def test_main_records_apply_failure_and_exits_nonzero(tmp_path, monkeypatch):
    report = tmp_path / 'review.csv'
    write_report(
        [ReviewRecord(tag='artist_tag', proposed_category='artist', source='rule34', status='planned_change')],
        report,
    )
    szuru = StubSzuru()
    szuru.category_error = RuntimeError('permission denied')

    monkeypatch.setattr(categorize_tags, 'config', make_settings(report))
    monkeypatch.setattr(szurubooru_toolkit, 'szuru', szuru, raising=False)

    try:
        categorize_tags.main(apply=True, from_report=str(report))
    except click.ClickException as error:
        assert 'Failed to apply 1 category change' in str(error)
    else:
        raise AssertionError('Apply failure returned success')

    assert szuru.updated == []
    assert read_report(report)[0].status == 'apply_failed'
