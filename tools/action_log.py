#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"

REQUIRED_FIELDS = {"session_id", "milestone", "action", "status"}
VALID_STATUS = {"verified", "failed", "mistake_detected", "repaired_verified", "pid_check"}


def log_path(session_id):
    d = RUNS_DIR / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "action_log.jsonl"


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


def next_seq(session_id):
    entries = _read_entries(session_id)
    return (entries[-1]["seq"] + 1) if entries else 1


def _append_one(data):
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        print(f"ERROR: missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)
    if data["status"] not in VALID_STATUS:
        print(f"ERROR: invalid status '{data['status']}', must be one of {VALID_STATUS}", file=sys.stderr)
        sys.exit(1)
    data["seq"] = next_seq(data["session_id"])
    data.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(log_path(data["session_id"]), "a") as f:
        f.write(json.dumps(data) + "\n")
    print(f"appended seq={data['seq']} status={data['status']}")


def cmd_append(args):
    loaded = json.loads(Path(args.data_file).read_text())
    # A data file may hold one entry (dict) or several (list) -- several is for
    # batching a set of independently-verified sub-steps that came back from a
    # single Blender call (e.g. a loop that added N ring details, each with its
    # own real before/after), so we don't need one MCP round-trip per entry.
    entries = loaded if isinstance(loaded, list) else [loaded]
    for data in entries:
        _append_one(data)


def cmd_summarize(args):
    entries = _read_entries(args.session)
    if not entries:
        print("no entries")
        return
    statuses = {}
    pids = set()
    for e in entries:
        statuses[e["status"]] = statuses.get(e["status"], 0) + 1
        if "pid" in e:
            pids.add(e["pid"])
    print(json.dumps({
        "total_entries": len(entries),
        "status_breakdown": statuses,
        "distinct_pids": list(pids),
        "first_ts": entries[0].get("ts"),
        "last_ts": entries[-1].get("ts"),
    }, indent=2))


def cmd_verify_count(args):
    entries = _read_entries(args.session)
    verified_statuses = {"verified", "repaired_verified"}
    verified = [e for e in entries if e["status"] in verified_statuses]
    pids = {e["pid"] for e in entries if "pid" in e}
    ok = len(verified) >= args.min and len(pids) == 1
    print(json.dumps({
        "verified_count": len(verified),
        "min_required": args.min,
        "distinct_pids": list(pids),
        "single_process": len(pids) == 1,
        "pass": ok,
    }, indent=2))
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append")
    p_append.add_argument("--data-file", required=True)
    p_append.set_defaults(func=cmd_append)

    p_sum = sub.add_parser("summarize")
    p_sum.add_argument("--session", required=True)
    p_sum.set_defaults(func=cmd_summarize)

    p_vc = sub.add_parser("verify-count")
    p_vc.add_argument("--session", required=True)
    p_vc.add_argument("--min", type=int, default=100)
    p_vc.set_defaults(func=cmd_verify_count)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
