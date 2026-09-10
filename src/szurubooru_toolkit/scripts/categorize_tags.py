from __future__ import annotations

import csv
import os
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

import click
from loguru import logger
from tqdm import tqdm

from szurubooru_toolkit import config
from szurubooru_toolkit.danbooru import DanbooruTagLookupError
from szurubooru_toolkit.rule34 import Rule34Error
from szurubooru_toolkit.rule34 import Rule34TagResult
from szurubooru_toolkit.szurubooru import SzurubooruApiError
from szurubooru_toolkit.szurubooru import Tag


DANBOORU_CATEGORIES = {
    0: 'default',
    1: 'artist',
    3: 'copyright',
    4: 'character',
    5: 'metadata',
}

CATEGORY_ORDER = ('artist', 'copyright', 'character', 'metadata')
CATEGORY_COLORS = {
    'artist': '#c00000',
    'copyright': '#a0a0ff',
    'character': '#00aa00',
    'metadata': '#ff7e00',
}

REPORT_FIELDS = (
    'tag',
    'matched_name',
    'usages',
    'current_category',
    'proposed_category',
    'source',
    'source_type',
    'source_post_count',
    'ambiguous',
    'lookup_mode',
    'status',
    'detail',
)

REPORT_STATUSES = {
    'planned_change',
    'resolved_unchanged',
    'not_found',
    'unsupported_source_type',
    'lookup_error',
    'applied',
    'skipped_changed',
    'apply_failed',
}

MUTATION_STATUSES = {'planned_change', 'applied', 'skipped_changed', 'apply_failed'}


@dataclass
class ReviewRecord:
    tag: str
    matched_name: str = ''
    usages: int = 0
    current_category: str = 'default'
    proposed_category: str = ''
    source: str = ''
    source_type: str = ''
    source_post_count: int | None = None
    ambiguous: bool = False
    lookup_mode: str = ''
    status: str = 'not_found'
    detail: str = ''


@dataclass
class _PendingTag:
    tag: Tag
    unsupported: Rule34TagResult | None = None
    rule34_error: Rule34Error | None = None


def _resolved_record(
    tag: Tag,
    matched_name: str,
    category: str,
    source: str,
    source_type: str,
    source_post_count: int | None = None,
    ambiguous: bool = False,
    lookup_mode: str = 'api',
) -> ReviewRecord:
    status = 'resolved_unchanged' if category == tag.category else 'planned_change'
    return ReviewRecord(
        tag=tag.primary_name,
        matched_name=matched_name,
        usages=tag.usages or 0,
        current_category=tag.category,
        proposed_category=category,
        source=source,
        source_type=source_type,
        source_post_count=source_post_count,
        ambiguous=ambiguous,
        lookup_mode=lookup_mode,
        status=status,
    )


def _resolve_rule34(tag: Tag, rule34) -> ReviewRecord | _PendingTag:
    unsupported = None
    first_error = None

    for name in tag.names:
        try:
            result = rule34.lookup(name)
        except Rule34Error as error:
            first_error = first_error or error
            continue

        if result is None:
            continue
        if result.category is None:
            unsupported = unsupported or result
            continue

        return _resolved_record(
            tag,
            result.name,
            result.category,
            'rule34',
            result.raw_type,
            result.post_count,
            result.ambiguous,
            result.lookup_mode,
        )

    return _PendingTag(tag=tag, unsupported=unsupported, rule34_error=first_error)


def resolve_tags(tags: list[Tag], rule34, danbooru, workers: int = 4, hide_progress: bool = False) -> list[ReviewRecord]:
    """Resolve local tag categories with Rule34 first and Danbooru second."""

    if workers <= 1:
        rule34_results = map(lambda tag: _resolve_rule34(tag, rule34), tags)
    else:
        executor = ThreadPoolExecutor(max_workers=workers)
        rule34_results = executor.map(lambda tag: _resolve_rule34(tag, rule34), tags)

    try:
        first_pass = list(tqdm(rule34_results, total=len(tags), ncols=80, leave=False, disable=hide_progress))
    finally:
        if workers > 1:
            executor.shutdown(wait=True)

    records = [result for result in first_pass if isinstance(result, ReviewRecord)]
    pending = [result for result in first_pass if isinstance(result, _PendingTag)]

    if not pending:
        return records

    names = list(dict.fromkeys(name for item in pending for name in item.tag.names))
    try:
        danbooru_categories = danbooru.get_tag_categories(names, strict=True)
    except DanbooruTagLookupError as error:
        for item in pending:
            details = []
            if item.rule34_error:
                details.append(f'Rule34: {item.rule34_error}')
            details.append(f'Danbooru: {error}')
            records.append(
                ReviewRecord(
                    tag=item.tag.primary_name,
                    usages=item.tag.usages or 0,
                    current_category=item.tag.category,
                    status='lookup_error',
                    detail='; '.join(details),
                )
            )
        return records

    categories_by_name = {name.casefold(): category for name, category in danbooru_categories.items()}
    for item in pending:
        match = next(
            ((name, categories_by_name[name.casefold()]) for name in item.tag.names if name.casefold() in categories_by_name),
            None,
        )

        if match:
            matched_name, numerical_category = match
            category = DANBOORU_CATEGORIES.get(numerical_category)
            if category:
                records.append(
                    _resolved_record(
                        item.tag,
                        matched_name,
                        category,
                        'danbooru',
                        str(numerical_category),
                    )
                )
            else:
                records.append(
                    ReviewRecord(
                        tag=item.tag.primary_name,
                        matched_name=matched_name,
                        usages=item.tag.usages or 0,
                        current_category=item.tag.category,
                        source='danbooru',
                        source_type=str(numerical_category),
                        lookup_mode='api',
                        status='unsupported_source_type',
                        detail='Danbooru returned an unsupported tag category',
                    )
                )
        elif item.unsupported:
            records.append(
                ReviewRecord(
                    tag=item.tag.primary_name,
                    matched_name=item.unsupported.name,
                    usages=item.tag.usages or 0,
                    current_category=item.tag.category,
                    source='rule34',
                    source_type=item.unsupported.raw_type,
                    source_post_count=item.unsupported.post_count,
                    ambiguous=item.unsupported.ambiguous,
                    lookup_mode=item.unsupported.lookup_mode,
                    status='unsupported_source_type',
                    detail='Rule34 returned an unsupported tag type; tag was not found on Danbooru',
                )
            )
        elif item.rule34_error:
            records.append(
                ReviewRecord(
                    tag=item.tag.primary_name,
                    usages=item.tag.usages or 0,
                    current_category=item.tag.category,
                    status='lookup_error',
                    detail=f'Rule34: {item.rule34_error}; tag was not found on Danbooru',
                )
            )
        else:
            records.append(
                ReviewRecord(
                    tag=item.tag.primary_name,
                    usages=item.tag.usages or 0,
                    current_category=item.tag.category,
                    status='not_found',
                    detail='Tag was not found on Rule34 or Danbooru',
                )
            )

    return records


def _report_sort_key(record: ReviewRecord) -> tuple:
    priority = {
        'lookup_error': 0,
        'not_found': 1,
        'unsupported_source_type': 2,
        'planned_change': 3,
        'apply_failed': 4,
        'skipped_changed': 5,
        'resolved_unchanged': 6,
        'applied': 7,
    }
    return priority.get(record.status, 99), -record.usages, record.tag.casefold()


def write_report(records: list[ReviewRecord], report_file: str | Path) -> Path:
    """Atomically write the complete category review CSV."""

    path = Path(report_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            newline='',
            prefix=f'.{path.name}.',
            suffix='.tmp',
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            writer = csv.DictWriter(temporary, fieldnames=REPORT_FIELDS)
            writer.writeheader()
            for record in sorted(records, key=_report_sort_key):
                writer.writerow(asdict(record))
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
        raise

    return path


def read_report(report_file: str | Path) -> list[ReviewRecord]:
    """Read and validate a previously generated review CSV."""

    records = []
    seen = set()

    with Path(report_file).open(encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not set(REPORT_FIELDS).issubset(reader.fieldnames):
            raise ValueError('Category report has an invalid or outdated header')

        for row in reader:
            tag_name = row['tag']
            normalized_name = tag_name.casefold()
            if not tag_name or tag_name != tag_name.strip() or normalized_name in seen:
                raise ValueError(f'Category report contains an empty or duplicate tag: {tag_name!r}')
            if row['status'] not in REPORT_STATUSES:
                raise ValueError(f'Category report contains an invalid status for "{tag_name}": {row["status"]!r}')
            if row['proposed_category'] and row['proposed_category'] not in ('default', *CATEGORY_ORDER):
                raise ValueError(
                    f'Category report contains an unsupported proposed category for "{tag_name}": {row["proposed_category"]!r}'
                )
            if row['current_category'] != 'default':
                raise ValueError(f'Category report contains a non-default source category for "{tag_name}"')
            if row['source'] not in ('', 'rule34', 'danbooru'):
                raise ValueError(f'Category report contains an invalid source for "{tag_name}": {row["source"]!r}')
            if row['lookup_mode'] not in ('', 'api', 'html'):
                raise ValueError(f'Category report contains an invalid lookup mode for "{tag_name}": {row["lookup_mode"]!r}')
            ambiguous_value = row['ambiguous'].casefold()
            if ambiguous_value not in ('true', 'false'):
                raise ValueError(f'Category report contains an invalid ambiguous flag for "{tag_name}"')
            if row['status'] in MUTATION_STATUSES and row['proposed_category'] not in CATEGORY_ORDER:
                raise ValueError(f'Category report contains no actionable category for "{tag_name}"')
            if row['status'] == 'resolved_unchanged' and row['proposed_category'] != row['current_category']:
                raise ValueError(f'Category report marks "{tag_name}" unchanged but its categories differ')
            if row['status'] in ('not_found', 'unsupported_source_type', 'lookup_error') and row['proposed_category']:
                raise ValueError(f'Category report gives unresolved tag "{tag_name}" an actionable category')

            try:
                usages = int(row['usages'] or 0)
                source_post_count = int(row['source_post_count']) if row['source_post_count'] else None
            except ValueError as error:
                raise ValueError(f'Category report contains an invalid count for "{tag_name}"') from error
            if usages < 0 or (source_post_count is not None and source_post_count < 0):
                raise ValueError(f'Category report contains a negative count for "{tag_name}"')

            seen.add(normalized_name)
            records.append(
                ReviewRecord(
                    tag=tag_name,
                    matched_name=row['matched_name'],
                    usages=usages,
                    current_category=row['current_category'],
                    proposed_category=row['proposed_category'],
                    source=row['source'],
                    source_type=row['source_type'],
                    source_post_count=source_post_count,
                    ambiguous=ambiguous_value == 'true',
                    lookup_mode=row['lookup_mode'],
                    status=row['status'],
                    detail=row['detail'],
                )
            )

    return records


def apply_records(records: list[ReviewRecord], szuru, category_colors: dict[str, str] = None) -> None:
    """Create required categories and apply planned category-only tag updates."""

    colors = CATEGORY_COLORS | (category_colors or {})
    planned = [record for record in records if record.status in ('planned_change', 'apply_failed')]
    if not planned:
        return

    required = {record.proposed_category for record in planned if record.proposed_category != 'default'}

    try:
        categories = szuru.get_tag_categories()
        existing = {category.name.casefold() for category in categories}
        next_order = max((category.order for category in categories), default=0) + 1

        for category_name in CATEGORY_ORDER:
            if category_name in required and category_name.casefold() not in existing:
                szuru.create_tag_category(category_name, colors[category_name], next_order)
                existing.add(category_name.casefold())
                next_order += 1
    except Exception as error:
        for record in planned:
            record.status = 'apply_failed'
            record.detail = f'Category setup failed before tag updates: {error}'
        return

    for record in planned:
        try:
            tag = szuru.get_tag(record.tag)
            if tag.category != 'default':
                record.status = 'skipped_changed'
                record.detail = f'Tag category changed concurrently to {tag.category!r}'
                continue

            szuru.update_tag_category(tag.primary_name, tag.version, record.proposed_category)
            record.status = 'applied'
            record.detail = ''
        except SzurubooruApiError as error:
            if 'version' in error.description.casefold() or 'modified' in error.name.casefold():
                record.status = 'skipped_changed'
                record.detail = 'Tag changed concurrently before the category update'
            else:
                record.status = 'apply_failed'
                record.detail = str(error)
        except Exception as error:
            record.status = 'apply_failed'
            record.detail = str(error)


def should_apply(explicit_apply: bool, report_only: bool, interactive: bool | None = None) -> bool:
    if explicit_apply:
        return True
    if report_only:
        return False
    if interactive is None:
        interactive = sys.stdin.isatty()
    if not interactive:
        return False
    return click.prompt('Choose next action', type=click.Choice(['save', 'apply']), default='save') == 'apply'


def _log_summary(records: list[ReviewRecord]) -> None:
    counts = Counter(record.status for record in records)
    logger.info(', '.join(f'{status}: {count}' for status, count in sorted(counts.items())))


def main(apply: bool = False, report_only: bool = False, from_report: str = '') -> None:
    from szurubooru_toolkit import szuru

    settings = config.categorize_tags
    report_file = Path(from_report or settings['report_file'])

    if apply and report_only:
        raise click.UsageError('--apply and --report-only cannot be used together.')

    if from_report:
        records = read_report(from_report)
    else:
        from szurubooru_toolkit import danbooru
        from szurubooru_toolkit import rule34

        tags = list(szuru.get_tags('category:default sort:usages'))
        logger.info(f'Found {len(tags)} default tag(s). Start resolving categories...')
        records = resolve_tags(
            tags,
            rule34,
            danbooru,
            workers=int(settings['workers']),
            hide_progress=config.globals.get('hide_progress', settings['hide_progress']),
        )
        write_report(records, report_file)
        _log_summary(records)
        logger.info(f'Wrote category review report to {report_file}')

    if should_apply(apply, report_only):
        apply_records(records, szuru, settings['category_colors'])
        write_report(records, report_file)
        _log_summary(records)
        failures = sum(record.status == 'apply_failed' for record in records)
        if failures:
            raise click.ClickException(f'Failed to apply {failures} category change(s). See {report_file} for details.')
        logger.success(f'Finished applying category changes and updated report {report_file}')
    else:
        logger.success(f'Saved category review report to {report_file}; no categories were changed.')


if __name__ == '__main__':
    main()
