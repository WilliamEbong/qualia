"""Export the API contract without starting a server or opening a project."""

import json
from pathlib import Path

from qualia.server.app import create_app

if __name__ == '__main__':
    # LF on every platform: the repository stores text files with LF endings.
    Path('openapi.json').write_text(json.dumps(create_app().openapi(), indent=2) + '\n',
                                    encoding='utf-8', newline='\n')
