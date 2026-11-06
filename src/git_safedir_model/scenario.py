"""Load a JSON scenario and run it under every mode."""
from __future__ import annotations

import json
from pathlib import Path

from .discovery import MODES, Env, discover
from .fs import MemFS


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def build(sc: dict) -> tuple[MemFS, Env]:
    e = dict(sc["env"])
    if "global" in e:
        e["global_"] = e.pop("global")
    return MemFS.from_spec(sc["fs"]), Env(**e)


def run(sc: dict) -> dict:
    fs, env = build(sc)
    return {m: discover(fs, sc["cwd"], env, m).to_dict() for m in MODES}
