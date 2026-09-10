import httpx
import pytest

from szurubooru_toolkit.rule34 import Rule34
from szurubooru_toolkit.rule34 import Rule34ResponseError
from szurubooru_toolkit.rule34 import Rule34TransientError


TAG_PAGE = """
<html><body><table>
<tr><th>Posts</th><th>Name</th><th>Type</th></tr>
<tr><td>49,052</td><td><a href="/posts">kantai_collection</a></td><td>Copyright (<a href="/edit">edit</a>)</tr>
</table></body></html>
"""


def test_parse_api_result():
    data = [{'tag_info': [{'tag': 'atdan', 'count': 86, 'type': 'artist'}]}]

    result = Rule34.parse_api_result(data, 'atdan')

    assert result.name == 'atdan'
    assert result.raw_type == 'artist'
    assert result.category == 'artist'
    assert result.post_count == 86
    assert result.lookup_mode == 'api'


def test_parse_api_result_requires_exact_name():
    data = [{'tag_info': [{'tag': 'kantai_collection_(anime)', 'count': 1, 'type': 'copyright'}]}]
    assert Rule34.parse_api_result(data, 'kantai_collection') is None


def test_parse_api_result_preserves_unknown_type():
    result = Rule34.parse_api_result([{'tag_info': [{'tag': 'custom_tag', 'count': 2, 'type': 'species'}]}], 'custom_tag')
    assert result.raw_type == 'species'
    assert result.category is None


def test_parse_api_result_uses_rule34_numeric_types():
    result = Rule34.parse_api_result([{'tag_info': [{'tag': 'character_tag', 'count': 2, 'type': 2}]}], 'character_tag')
    assert result.category == 'character'


def test_parse_api_result_recognizes_generic_and_ambiguous_tags():
    data = [{'tag_info': [{'tag': 'ambiguous_tag', 'count': 2, 'type': 'tag', 'ambiguous': True}]}]
    result = Rule34.parse_api_result(data, 'AMBIGUOUS_TAG')

    assert result.category == 'default'
    assert result.ambiguous is True


def test_parse_html_result():
    result = Rule34.parse_html_result(TAG_PAGE, 'kantai_collection')

    assert result.name == 'kantai_collection'
    assert result.raw_type == 'Copyright'
    assert result.category == 'copyright'
    assert result.post_count == 49052
    assert result.lookup_mode == 'html'


def test_parse_html_result_requires_expected_table():
    with pytest.raises(Rule34ResponseError):
        Rule34.parse_html_result('<html><body>challenge</body></html>', 'kantai_collection')


def test_lookup_api_sends_credentials_and_caches_result():
    requests = []

    def handler(request):
        requests.append(request)
        params = dict(request.url.params)
        assert params['s'] == 'post'
        assert params['tags'] == 'atdan'
        assert params['limit'] == '1'
        assert params['fields'] == 'tag_info'
        assert params['user_id'] == '42'
        assert params['api_key'] == 'secret'
        return httpx.Response(200, json=[{'tag_info': [{'tag': 'atdan', 'count': 86, 'type': 'artist'}]}])

    client = Rule34(user_id=42, api_key='secret', mode='api', transport=httpx.MockTransport(handler))

    assert client.lookup('atdan').category == 'artist'
    assert client.lookup('atdan').category == 'artist'
    assert len(requests) == 1


def test_api_mode_requires_credentials():
    with pytest.raises(ValueError, match='requires both'):
        Rule34(mode='api', transport=httpx.MockTransport(lambda request: httpx.Response(500)))


def test_credentials_must_be_configured_as_a_pair():
    with pytest.raises(ValueError, match='both be configured'):
        Rule34(user_id=42, mode='auto')


def test_empty_api_result_is_cached_as_not_found():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[])

    client = Rule34(user_id=42, api_key='secret', mode='api', transport=httpx.MockTransport(handler))

    assert client.lookup('missing') is None
    assert client.lookup('missing') is None
    assert len(requests) == 1


def test_http_404_is_a_source_error():
    client = Rule34(
        user_id=42,
        api_key='secret',
        mode='api',
        transport=httpx.MockTransport(lambda request: httpx.Response(404)),
    )

    with pytest.raises(Rule34ResponseError, match='HTTP 404'):
        client.lookup('missing')


def test_retry_after_is_honored_and_transient_failures_are_not_cached():
    requests = []
    sleeps = []
    now = [0.0]

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def handler(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(429, headers={'Retry-After': '2.5'})
        return httpx.Response(200, json=[{'tag_info': [{'tag': 'atdan', 'count': 86, 'type': 'artist'}]}])

    client = Rule34(
        user_id=42,
        api_key='secret',
        mode='api',
        retries=2,
        transport=httpx.MockTransport(handler),
        sleep=sleep,
        clock=lambda: now[0],
    )

    assert client.lookup('atdan').category == 'artist'
    assert sleeps == [2.5]
    assert len(requests) == 2


def test_malformed_responses_are_not_cached():
    responses = [httpx.Response(200, json={'unexpected': True}), httpx.Response(200, json=[])]
    client = Rule34(
        user_id=42,
        api_key='secret',
        mode='api',
        transport=httpx.MockTransport(lambda request: responses.pop(0)),
    )

    with pytest.raises(Rule34ResponseError):
        client.lookup('missing')
    assert client.lookup('missing') is None


def test_final_rate_limit_still_sets_shared_cooldown():
    client = Rule34(
        user_id=42,
        api_key='secret',
        mode='api',
        retries=1,
        transport=httpx.MockTransport(lambda request: httpx.Response(429, headers={'Retry-After': '3'})),
        clock=lambda: 10.0,
    )

    with pytest.raises(Rule34TransientError):
        client.lookup('atdan')
    assert client._resume_at == 13.0


def test_auto_mode_falls_back_to_html_after_authentication_error():
    def handler(request):
        if request.url.host == 'api.rule34.xxx':
            return httpx.Response(401, text='Missing authentication')
        return httpx.Response(200, text=TAG_PAGE)

    client = Rule34(
        user_id=42,
        api_key='invalid',
        mode='auto',
        html_delay=0,
        transport=httpx.MockTransport(handler),
    )

    result = client.lookup('kantai_collection')
    assert result.category == 'copyright'
    assert result.lookup_mode == 'html'


def test_html_mode_returns_none_for_exact_miss():
    client = Rule34(mode='html', html_delay=0, transport=httpx.MockTransport(lambda request: httpx.Response(200, text=TAG_PAGE)))
    assert client.lookup('missing_tag') is None
