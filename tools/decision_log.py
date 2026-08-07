#!/usr/bin/env python3
"""Stricter decision-cycle log for Proof 1. Unlike action_log.py (which only
records that an operation happened and was verified), this requires each
entry to prove it was part of a genuine observe -> decide -> act -> verify
cycle, chained to the previous one via Blender's own live revision counter
(blender_ops/decision_state.py) -- not a value this script invents.

A batch of pre-planned actions run inside one Blender call cannot pass
`verify-count` here: they'd all carry the same or overlapping
observation_revision, and their timestamps would land within the same
sub-second window. Both are checked.
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"

REQUIRED_FIELDS = {
    "decision_id", "session_id", "pid", "observation_revision", "reason",
    "chosen_action", "result_revision", "evaluation",
}
VALID_EVALUATIONS = {"accepted", "rejected", "mistake_detected", "repaired", "reverted"}

MIN_CYCLE_SECONDS = 1.0  # consecutive decisions closer than this look batched


def log_path(session_id):
    d = RUNS_DIR / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "decision_log.jsonl"


def _read_entries(session_id):
    path = log_path(session_id)
    entries = []
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries


def _parse_ts(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def cmd_append(args):
    data = json.loads(Path(args.data_file).read_text())
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        print(f"ERROR: missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)
    if data["evaluation"] not in VALID_EVALUATIONS:
        print(f"ERROR: invalid evaluation '{data['evaluation']}'", file=sys.stderr)
        sys.exit(1)
    if data["evaluation"] == "reverted":
        # A "reverted" entry documents the live scene's revision moving BACKWARD from what
        # the log's last entry claimed -- e.g. someone pressed undo in the Blender GUI and it
        # rolled back a scripted decision along with their own edit. This is the one entry
        # type allowed to violate the normal +1-per-decision rule, because it isn't recording
        # a new decision -- it's recording that reality diverged from the log and by how much.
        if data["result_revision"] >= data["observation_revision"]:
            print(
                f"ERROR: a 'reverted' entry must show result_revision < observation_revision "
                f"(a regression) -- got {data['observation_revision']} -> "
                f"{data['result_revision']}", file=sys.stderr)
            sys.exit(1)
    elif data["result_revision"] != data["observation_revision"] + 1:
        print(
            f"ERROR: result_revision ({data['result_revision']}) must be exactly "
            f"observation_revision+1 ({data['observation_revision'] + 1}) -- more than "
            f"one mutation happened in this decision", file=sys.stderr)
        sys.exit(1)

    entries = _read_entries(data["session_id"])
    if entries:
        prev = entries[-1]
        if data["observation_revision"] != prev["result_revision"]:
            print(
                f"ERROR: this decision observed revision {data['observation_revision']}, but "
                f"the previous decision (seq {prev['seq']}) left the scene at revision "
                f"{prev['result_revision']} -- re-observe current state before deciding",
                file=sys.stderr)
            sys.exit(1)

    data["seq"] = (entries[-1]["seq"] + 1) if entries else 1
    data.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    with open(log_path(data["session_id"]), "a") as f:
        f.write(json.dumps(data) + "\n")
    print(f"appended seq={data['seq']} decision_id={data['decision_id']} "
          f"revision {data['observation_revision']}->{data['result_revision']}")


def cmd_verify_count(args):
    entries = _read_entries(args.session)
    problems = []

    pids = {e["pid"] for e in entries}
    if len(pids) != 1:
        problems.append(f"expected exactly one PID across the log, found {pids}")

    for i in range(1, len(entries)):
        prev, cur = entries[i - 1], entries[i]
        if cur["observation_revision"] != prev["result_revision"]:
            problems.append(
                f"seq {cur['seq']}: observation_revision {cur['observation_revision']} != "
                f"previous result_revision {prev['result_revision']} (gap or overlap)")
        try:
            gap = (_parse_ts(cur["ts"]) - _parse_ts(prev["ts"])).total_seconds()
            if gap < MIN_CYCLE_SECONDS:
                problems.append(
                    f"seq {prev['seq']}->{cur['seq']}: only {gap:.2f}s apart "
                    f"(< {MIN_CYCLE_SECONDS}s) -- looks batched, not a real round-trip")
        except (KeyError, ValueError):
            problems.append(f"seq {cur['seq']}: missing/invalid timestamp")

    accepted = [e for e in entries if e["evaluation"] in ("accepted", "repaired")]
    ok = len(accepted) >= args.min and not problems

    print(json.dumps({
        "decision_count": len(entries),
        "accepted_or_repaired_count": len(accepted),
        "min_required": args.min,
        "distinct_pids": list(pids),
        "revision_chain_and_timing_problems": problems,
        "pass": ok,
    }, indent=2))
    sys.exit(0 if ok else 1)


def cmd_summarize(args):
    entries = _read_entries(args.session)
    if not entries:
        print("no entries")
        return
    evals = {}
    for e in entries:
        evals[e["evaluation"]] = evals.get(e["evaluation"], 0) + 1
    print(json.dumps({
        "total_entries": len(entries),
        "evaluation_breakdown": evals,
        "revision_span": [entries[0]["observation_revision"], entries[-1]["result_revision"]],
        "first_ts": entries[0].get("ts"),
        "last_ts": entries[-1].get("ts"),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append")
    p_append.add_argument("--data-file", required=True)
    p_append.set_defaults(func=cmd_append)

    p_vc = sub.add_parser("verify-count")
    p_vc.add_argument("--session", required=True)
    p_vc.add_argument("--min", type=int, default=100)
    p_vc.set_defaults(func=cmd_verify_count)

    p_sum = sub.add_parser("summarize")
    p_sum.add_argument("--session", required=True)
    p_sum.set_defaults(func=cmd_summarize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
