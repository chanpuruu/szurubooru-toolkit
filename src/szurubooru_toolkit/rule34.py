from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Callable

import httpx
from loguru import logger

from szurubooru_toolkit.boorus import USER_AGENT


API_URL = 'https://api.rule34.xxx/index.php'
TAG_PAGE_URL = 'https://rule34.xxx/index.php'
TRANSIENT_STATUS_CODES = (429, 500, 502, 503, 504)

NUMERIC_TYPES = {
    0: ('General', 'default'),
    1: ('Artist', 'artist'),
    2: ('Character', 'character'),
    3: ('Copyright', 'copyright'),
    4: ('Metadata', 'metadata'),
}

STRING_TYPES = {
    'general': 'default',
    'tag': 'default',
    'artist': 'artist',
    'copyright': 'copyright',
    'character': 'character',
    'metadata': 'metadata',
    'meta': 'metadata',
}


class Rule34Error(Exception):
    """Base error for Rule34 tag metadata lookups."""


class Rule34AuthenticationError(Rule34Error):
    """Raised when authenticated Rule34 API access is unavailable."""


class Rule34TransientError(Rule34Error):
    """Raised when Rule34 remains unavailable after retries."""


class Rule34ResponseError(Rule34Error):
    """Raised when Rule34 returns a response that cannot be trusted."""


@dataclass(frozen=True)
class Rule34TagResult:
    name: str
    raw_type: str
    category: str | None
    post_count: int | None
    ambiguous: bool
    lookup_mode: str


class _TagPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == 'tr':
            self._row = []
        elif tag in ('td', 'th') and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ('td', 'th') and self._cell is not None and self._row is not None:
            self._row.append(' '.join(''.join(self._cell).split()))
            self._cell = None
        elif tag == 'tr' and self._row is not None:
            if self._cell is not None:
                self._row.append(' '.join(''.join(self._cell).split()))
            if self._row:
                self.rows.append(self._row)
            self._row = None
            self._cell = None


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).casefold() in ('1', 'true', 'yes')


def _parse_count(value: object) -> int | None:
    if value is None:
        return None
    digits = re.sub(r'[^0-9]', '', str(value))
    return int(digits) if digits else None


def _normalize_type(value: object) -> tuple[str, str | None]:
    try:
        numeric_type = int(value)
    except (TypeError, ValueError):
        raw_type = str(value).strip()
        base_type = raw_type.split(',', 1)[0].casefold()
        return raw_type, STRING_TYPES.get(base_type)

    return NUMERIC_TYPES.get(numeric_type, (str(numeric_type), None))


class Rule34:
    """Look up exact Rule34 tag types through its API or public tag page."""

    def __init__(
        self,
        user_id: str | int | None = None,
        api_key: str | None = None,
        mode: str = 'auto',
        retries: int = 3,
        backoff: float = 2.0,
        html_delay: float = 1.0,
        transport: httpx.BaseTransport = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if mode not in ('auto', 'api', 'html'):
            raise ValueError(f'Unknown Rule34 lookup mode: {mode}')

        self.user_id = str(user_id) if user_id not in (None, '', 'None') else None
        self.api_key = api_key if api_key not in (None, '', 'None') else None
        if bool(self.user_id) != bool(self.api_key):
            raise ValueError('Rule34 user_id and api_key must either both be configured or both be omitted')
        if mode == 'api' and not (self.user_id and self.api_key):
            raise ValueError('Rule34 API mode requires both user_id and api_key')

        self.mode = mode
        self.retries = max(1, retries)
        self.backoff = max(0.0, backoff)
        self.html_delay = max(0.0, html_delay)
        self._sleep = sleep
        self._clock = clock
        self._cache: dict[tuple[str, str], Rule34TagResult | None] = {}
        self._cache_lock = threading.Lock()
        self._cooldown_lock = threading.Lock()
        self._resume_at = 0.0
        self._html_lock = threading.Lock()
        self._last_html_request: float | None = None
        self.client = httpx.Client(
            headers={'User-Agent': USER_AGENT},
            follow_redirects=True,
            timeout=30,
            transport=transport,
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.user_id and self.api_key)

    def lookup(self, tag_name: str, mode: str | None = None) -> Rule34TagResult | None:
        """Return metadata for an exact tag name, or None for a genuine miss.

        Successful results and genuine misses are cached. Source failures are not
        cached so a later lookup can recover from a temporary outage.
        """

        lookup_mode = mode or self.mode
        if lookup_mode not in ('auto', 'api', 'html'):
            raise ValueError(f'Unknown Rule34 lookup mode: {lookup_mode}')

        cache_key = (lookup_mode, tag_name.casefold())
        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        if lookup_mode == 'api':
            result = self.lookup_api(tag_name)
        elif lookup_mode == 'html':
            result = self.lookup_html(tag_name)
        else:
            result = self._lookup_auto(tag_name)

        with self._cache_lock:
            self._cache[cache_key] = result
        return result

    def _lookup_auto(self, tag_name: str) -> Rule34TagResult | None:
        if self.has_credentials:
            try:
                result = self.lookup(tag_name, mode='api')
                if result is not None:
                    return result
            except Rule34Error as error:
                logger.debug(f'Rule34 API lookup failed for "{tag_name}", falling back to the public tag page: {error}')

        return self.lookup(tag_name, mode='html')

    def lookup_api(self, tag_name: str) -> Rule34TagResult | None:
        if not self.has_credentials:
            raise Rule34AuthenticationError('Rule34 API mode requires both user_id and api_key')

        params = {
            'page': 'dapi',
            's': 'post',
            'q': 'index',
            'json': '1',
            'tags': tag_name,
            'limit': '1',
            'fields': 'tag_info',
            'user_id': self.user_id,
            'api_key': self.api_key,
        }
        response = self._get(API_URL, params)
        if response is None:
            return None
        if not response.content:
            return None

        try:
            data = response.json()
        except ValueError as error:
            raise Rule34ResponseError('Rule34 tag API returned malformed JSON') from error

        return self.parse_api_result(data, tag_name)

    def lookup_html(self, tag_name: str) -> Rule34TagResult | None:
        params = {'page': 'tags', 's': 'list', 'tags': tag_name, 'order_by': 'updated', 'sort': 'asc'}

        with self._html_lock:
            if self._last_html_request is not None:
                remaining = self.html_delay - (self._clock() - self._last_html_request)
                if remaining > 0:
                    self._sleep(remaining)
            response = self._get(TAG_PAGE_URL, params)
            self._last_html_request = self._clock()

        if response is None:
            return None
        return self.parse_html_result(response.text, tag_name)

    @staticmethod
    def parse_api_result(data: object, tag_name: str) -> Rule34TagResult | None:
        if not isinstance(data, list):
            raise Rule34ResponseError('Rule34 post API returned an unexpected response')

        entries = []
        for post in data:
            if not isinstance(post, dict) or not isinstance(post.get('tag_info'), list):
                raise Rule34ResponseError('Rule34 post API result did not contain tag_info')
            entries.extend(post['tag_info'])

        for entry in entries:
            if not isinstance(entry, dict) or str(entry.get('tag', '')).casefold() != tag_name.casefold():
                continue

            type_value = entry.get('type')
            if type_value is None:
                raise Rule34ResponseError(f'Rule34 API result for "{tag_name}" has no tag type')

            raw_type, category = _normalize_type(type_value)
            ambiguous = _parse_bool(entry.get('ambiguous', False))
            return Rule34TagResult(
                name=str(entry['tag']),
                raw_type=raw_type,
                category=category,
                post_count=_parse_count(entry.get('count')),
                ambiguous=ambiguous,
                lookup_mode='api',
            )

        return None

    @staticmethod
    def parse_html_result(content: str, tag_name: str) -> Rule34TagResult | None:
        parser = _TagPageParser()
        parser.feed(content)

        has_header = any(
            len(row) >= 3 and row[0].casefold() == 'posts' and row[1].casefold() == 'name' and row[2].casefold() == 'type'
            for row in parser.rows
        )
        if not has_header:
            raise Rule34ResponseError('Rule34 tag page did not contain the expected tag table')

        for row in parser.rows:
            if len(row) < 3 or row[1].casefold() != tag_name.casefold():
                continue

            raw_type = row[2].split('(', 1)[0].strip()
            _, category = _normalize_type(raw_type)
            return Rule34TagResult(
                name=row[1],
                raw_type=raw_type,
                category=category,
                post_count=_parse_count(row[0]),
                ambiguous='ambiguous' in raw_type.casefold(),
                lookup_mode='html',
            )

        return None

    def _get(self, url: str, params: dict) -> httpx.Response | None:
        for attempt in range(1, self.retries + 1):
            self._wait_for_cooldown()
            try:
                response = self.client.get(url, params=params)
            except httpx.TransportError as error:
                if attempt == self.retries:
                    raise Rule34TransientError('Rule34 request failed after retries') from error
                self._sleep(attempt * self.backoff)
                continue

            if response.status_code in (401, 403) or 'missing authentication' in response.text.casefold():
                raise Rule34AuthenticationError('Rule34 rejected the configured API credentials')

            if response.status_code in TRANSIENT_STATUS_CODES:
                delay = self._retry_delay(response, attempt)
                if response.status_code == 429:
                    self._set_cooldown(delay)
                elif attempt < self.retries:
                    self._sleep(delay)

                if attempt == self.retries:
                    raise Rule34TransientError(f'Rule34 returned HTTP {response.status_code} after retries')
                continue

            if response.is_error:
                raise Rule34ResponseError(f'Rule34 returned HTTP {response.status_code}')

            return response

        raise Rule34TransientError('Rule34 request failed after retries')

    def _wait_for_cooldown(self) -> None:
        with self._cooldown_lock:
            remaining = self._resume_at - self._clock()
        if remaining > 0:
            self._sleep(remaining)

    def _set_cooldown(self, seconds: float) -> None:
        with self._cooldown_lock:
            self._resume_at = max(self._resume_at, self._clock() + seconds)

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after).timestamp()
                    return max(0.0, retry_at - time.time())
                except (TypeError, ValueError, OverflowError):
                    pass
        return attempt * self.backoff
