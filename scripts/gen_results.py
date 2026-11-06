"""Regenerate results/ from the scenario fixtures (in-memory only)."""
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from git_safedir_model.discovery import MODES  # noqa: E402
from git_safedir_model.scenario import load, run  # noqa: E402


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    full, rows = {}, []
    for p in sorted((ROOT / "fixtures/scenarios").glob("*.json")):
        sc = load(p)
        r = run(sc)
        full[sc["name"]] = r
        for m in MODES:
            x = r[m]
            rows.append({"scenario": sc["name"], "mode": m, "kind": x["kind"], "ownership": x["ownership"] or "",
                         "checked_dir": x["worktree_or_dir"] or "", "repo_config_parsed": x["repo_config_parsed"],
                         "command_valued_keys": ";".join(x["command_valued_keys_in_repo_config"]),
                         "ignored_sources": ";".join(x["ignored_safe_directory_sources"]),
                         "visited": len(x["visited"])})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (out / "scenarios.csv").write_text(buf.getvalue())
    (out / "scenarios.json").write_text(json.dumps(full, indent=1, sort_keys=True) + "\n")
    names = ["scenarios.csv", "scenarios.json"]
    (out / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256((out / n).read_bytes()).hexdigest()}  {n}\n" for n in names))
    print(f"{len(full)} scenarios x {len(MODES)} modes -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results")
