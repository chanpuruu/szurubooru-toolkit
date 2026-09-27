"""Run the optional, read-only web scaffold independently of CLI config."""

import argparse

import uvicorn

from szurubooru_toolkit.web.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the read-only web scaffold (no command execution).')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    uvicorn.run(create_app(), host=args.host, port=args.port, workers=1)


if __name__ == '__main__':
    main()
