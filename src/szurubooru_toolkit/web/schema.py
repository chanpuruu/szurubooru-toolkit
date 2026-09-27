"""Export the public scaffold schema without opening a network listener."""

import json

from szurubooru_toolkit.web.app import create_app


if __name__ == '__main__':
    print(json.dumps(create_app().openapi(), sort_keys=True))
