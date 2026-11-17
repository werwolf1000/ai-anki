"""Executed with python -I in the disposable runtime, never on the API host."""
import base64
import json
import os
from pathlib import Path
import stat

root = Path('/workspace/artifacts')
allowed = {'.html', '.json', '.csv', '.txt', '.png', '.pt', '.sqlite'}
result, total = [], 0
if root.is_dir() and not root.is_symlink():
    for path in sorted(root.iterdir()):
        if len(result) >= 8:
            break
        if path.suffix.lower() not in allowed or len(path.name) > 120:
            continue
        try:
            # O_NOFOLLOW prevents a student process swapping a file for a symlink.
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 1_000_000:
                    continue
                data = stream.read(1_000_001)
            if len(data) > 1_000_000 or total + len(data) > 2_000_000:
                continue
            result.append({'name': path.name, 'data': base64.b64encode(data).decode('ascii'), 'size': len(data)})
            total += len(data)
        except OSError:
            continue
print(json.dumps(result))
