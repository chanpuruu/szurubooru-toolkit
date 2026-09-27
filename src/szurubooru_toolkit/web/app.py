"""Read-only API and explicit SPA serving boundaries."""

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles


class SystemStatus(BaseModel):
    service: Literal['szurubooru-toolkit'] = 'szurubooru-toolkit'
    mode: Literal['scaffold'] = 'scaffold'
    operations_enabled: Literal[False] = False
    static_ready: bool


def create_app(static_dir: Path | None = None) -> FastAPI:
    static_root = (
        static_dir if static_dir is not None else Path(os.environ.get('TOOLKIT_WEB_STATIC_DIR', Path(__file__).parent / 'static'))
    ).resolve()
    index_file = static_root / 'index.html'
    assets_dir = static_root / 'assets'
    app = FastAPI(title='Szurubooru Toolkit', version='0.1.0', docs_url=None, redoc_url=None, openapi_url=None)

    def static_ready() -> bool:
        return index_file.is_file() and assets_dir.is_dir()

    @app.get('/healthz')
    def health() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/readyz')
    def readiness() -> dict[str, str]:
        if not static_ready():
            raise HTTPException(status_code=503, detail='Frontend build unavailable')
        return {'status': 'ready', 'mode': 'scaffold'}

    @app.get('/api/v1/system/status', response_model=SystemStatus)
    def system_status() -> SystemStatus:
        return SystemStatus(static_ready=static_ready())

    if assets_dir.is_dir():
        app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

    @app.get('/', include_in_schema=False)
    @app.get('/system', include_in_schema=False)
    def frontend() -> FileResponse:
        if not static_ready():
            raise HTTPException(status_code=503, detail='Frontend build unavailable')
        return FileResponse(index_file, headers={'Cache-Control': 'no-cache'})

    return app
