"""Self-contained canvas replay; no CDN or local web server required."""
import json
from pathlib import Path

from .io import clean_json


def write_replay(path, record):
    template = Path(__file__).with_name("replay_template.html").read_text(encoding="utf-8")
    payload = json.dumps(clean_json(record), ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    Path(path).write_text(template.replace("__EPISODE_JSON__", payload), encoding="utf-8")

