#!/bin/sh
# Build practice images and create the shared key without restarting TrueNAS Apps.
set -eu
practice_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$practice_root"

docker info >/dev/null
python3 - <<'PY'
import os
from pathlib import Path
import secrets

path = Path('.secrets/practice-worker.env')
path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    entries = dict(line.split('=', 1) for line in path.read_text().splitlines()
                   if line.strip() and not line.lstrip().startswith('#') and '=' in line)
    if len(entries.get('AI_ANKI_PRACTICE_TOKEN', '')) < 32:
        raise SystemExit(f'{path}: expected an existing shared token of at least 32 characters')
else:
    with os.fdopen(fd, 'w') as stream:
        stream.write('AI_ANKI_PRACTICE_TOKEN=' + secrets.token_hex(32) + '\n')
path.chmod(0o600)
print(f'Shared key ready: {path.resolve()} (value hidden, existing key preserved)', flush=True)
PY

docker build -f practice/worker.Dockerfile -t ai-anki-practice-worker:1 .
docker build -f practice/Dockerfile --target base -t ai-anki-practice-base:1 .
docker build -f practice/Dockerfile --target data -t ai-anki-practice-data:1 .
docker build -f practice/Dockerfile --target ml -t ai-anki-practice-ml:1 .
docker compose -f docker-compose.truenas.practice.yml config --quiet
printf '%s\n' 'Ready. Replace the YAML of the existing TrueNAS App with docker-compose.truenas.practice.yml.'
