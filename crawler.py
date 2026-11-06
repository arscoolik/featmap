"""Resumable breadth-first collection shared by provider adapters."""
import json
import logging
from collections import deque
from pathlib import Path

from graph_data import load_data


def crawl(path, seeds, fetch, limit):
    path = Path(path)
    data = load_data(path) if path.exists() else {}
    queue = deque(dict.fromkeys([*seeds, *(f for r in data.values() for f in r['feats'])]))
    visited = set(data)
    count = 0
    try:
        while queue and count < limit:
            name = queue.popleft()
            if name in visited:
                continue
            visited.add(name)
            record = fetch(name)
            if record is None:
                continue
            # Preserve every observed collaborator, including already visited artists.
            record['feats'] = sorted(set(record['feats']) - {name})
            data[name] = record
            queue.extend(f for f in record['feats'] if f not in visited)
            count += 1
            logging.info("Collected %s (%d artists)", name, count)
            save(data, path)
    finally:
        save(data, path)


def save(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)
