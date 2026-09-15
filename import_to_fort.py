#!/usr/bin/env python3
"""Turn a Weekday Labeler export into Fort's parquet, via the local tool.

The web app deliberately writes no parquet: pyarrow does not run in a browser,
and re-implementing ground_truth.v3 in JavaScript would be a second thing to
keep in step with Fort's schema. Instead it exports the same working-draft JSON
the local tool keeps, and this drops that in as the local tool's working state.
Open the local app afterwards and press Export revision -- the code that has
already been checked against Fort's fixture does the rest.

    python3 import_to_fort.py ~/Downloads/guru_..._Priya__labels.json

Options are only needed when the local package is named differently from the
one the web data was baked from.
"""
import argparse, json, re, sys
from pathlib import Path

DEFAULT_DEMO = Path.home() / "Downloads" / "fort-annotator-demo"


def safe_name(s):                       # identical to server.py
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", (s or "").strip()) or "unset"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export", type=Path, help="JSON from the web app's Export button")
    ap.add_argument("--demo", type=Path, default=DEFAULT_DEMO,
                    help=f"fort-annotator-demo folder (default {DEFAULT_DEMO})")
    ap.add_argument("--labels-root", type=Path, default=None,
                    help="default <demo>/my_labels")
    ap.add_argument("--session-id", default=None,
                    help="session id as the LOCAL package names it; defaults to "
                         "the id in the export, which is right when both were "
                         "built from the same capture package")
    a = ap.parse_args()

    d = json.loads(a.export.read_text())
    if d.get("schema") != "fort.exercise_study_data.working_draft.v2":
        sys.exit(f"not a Weekday Labeler export: schema={d.get('schema')!r}")

    segs = d.get("segments") or []
    ex = [s for s in segs if s["label_type"] == "exercise"]
    if not ex:
        sys.exit("that export has no exercise intervals in it")

    labels_root = a.labels_root or (a.demo / "my_labels")
    sid = a.session_id or d["session_id"]
    out = labels_root / "_weekday_working" / sid
    out.mkdir(parents=True, exist_ok=True)
    state = out / f"working__{safe_name(d['labeler_id'])}.json"

    if state.exists():
        prev = json.loads(state.read_text()).get("segments", [])
        n = len([s for s in prev if s["label_type"] == "exercise"])
        if input(f"{state} already holds {n} exercise interval(s). Overwrite? [y/N] ").lower() != "y":
            sys.exit("left alone")

    state.write_text(json.dumps({
        "annotation_set_id": d["annotation_set_id"],
        "labeler_id": d["labeler_id"],
        "segments": segs,
    }, indent=2))

    span = max(s["end_s"] for s in segs)
    print(f"wrote {state}")
    print(f"  {len(ex)} exercise intervals, {len(segs)} rows, 0 - {span:.1f}s")
    print(f"  labeler {d['labeler_id']} · annotation set {d['annotation_set_id']}")
    print()
    print("Next: start the local tool (start.command), enter the SAME labeler id")
    print(f"  ({d['labeler_id']}), check the timings look right, then press Export revision.")


if __name__ == "__main__":
    main()
