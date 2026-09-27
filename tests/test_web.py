import pytest


pytest.importorskip('fastapi')

from fastapi.testclient import TestClient  # noqa E402

from szurubooru_toolkit.web.app import create_app  # noqa E402


@pytest.fixture
def static_root(tmp_path):
    (tmp_path / 'assets').mkdir()
    (tmp_path / 'assets' / 'app.js').write_text('console.log("scaffold")', encoding='utf-8')
    (tmp_path / 'index.html').write_text('<html>Toolkit</html>', encoding='utf-8')
    return tmp_path


def test_health_and_status_without_toolkit_initialization(tmp_path, monkeypatch):
    import szurubooru_toolkit

    def forbidden_setup():
        pytest.fail('Web scaffold must not load toolkit configuration or clients')

    monkeypatch.setattr(szurubooru_toolkit, 'setup_config', forbidden_setup)
    monkeypatch.setattr(szurubooru_toolkit, 'setup_clients', forbidden_setup)
    client = TestClient(create_app(tmp_path))
    assert client.get('/healthz').json() == {'status': 'ok'}
    assert client.get('/api/v1/system/status').json() == {
        'service': 'szurubooru-toolkit',
        'mode': 'scaffold',
        'operations_enabled': False,
        'static_ready': False,
    }
    assert client.get('/readyz').status_code == 503
    assert client.get('/').status_code == 503


def test_spa_routes_and_assets(static_root):
    client = TestClient(create_app(static_root))
    for path in ['/', '/system']:
        response = client.get(path)
        assert response.status_code == 200
        assert response.text == '<html>Toolkit</html>'
        assert response.headers['cache-control'] == 'no-cache'
    assert client.get('/assets/app.js').status_code == 200
    assert client.get('/readyz').json() == {'status': 'ready', 'mode': 'scaffold'}


@pytest.mark.parametrize(
    'path', ['/api', '/api/v1/jobs', '/docs', '/openapi.json', '/assets/missing.js', '/unknown', '/assets/%2e%2e/config.toml']
)
def test_unknown_paths_do_not_fall_back_to_html(static_root, path):
    client = TestClient(create_app(static_root))
    response = client.get(path)
    assert response.status_code == 404
    assert 'text/html' not in response.headers['content-type']


def test_no_mutating_api_or_permissive_cors(static_root):
    client = TestClient(create_app(static_root))
    assert client.post('/api/v1/jobs', json={}).status_code == 404
    assert client.get('/import-from-url?url=https://example.invalid').status_code == 404
    assert client.post('/import-from-all-tabs', json={'urls': ['https://example.invalid']}).status_code == 404
    assert client.post('/system').status_code == 405
    response = client.options('/api/v1/system/status', headers={'Origin': 'https://untrusted.example'})
    assert 'access-control-allow-origin' not in response.headers


def test_static_symlink_escape_is_denied(static_root, tmp_path_factory):
    outside = tmp_path_factory.mktemp('private') / 'secret.txt'
    outside.write_text('private', encoding='utf-8')
    try:
        (static_root / 'assets' / 'secret.txt').symlink_to(outside)
    except OSError:
        pytest.skip('Host does not permit symlink creation')
    client = TestClient(create_app(static_root))
    assert client.get('/assets/secret.txt').status_code == 404
