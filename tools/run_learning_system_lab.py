"""Exercise documentation crawl accounting and guarded self-session learning."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from knowledge_engine.ingest.document_ingest import crawl_local_documents
from knowledge_engine.session_learning import apply_replay_result, mine_session_events, read_decision_logs


def main():
    out=ROOT/"runs"/"2026-08-10_learning-system"; docs=out/"docs_fixture"; docs.mkdir(parents=True,exist_ok=True)
    (docs/"index.html").write_text("<h1>Modeling</h1><a href='bevel.html'>Bevel</a><a href='bevel-copy.html'>Duplicate</a><a href='notes.md'>Notes</a>",encoding="utf-8")
    bevel="<h1>Bevel</h1><h2>Options</h2><p>Parameter: width.</p><p>Warning: excessive width overlaps.</p>"
    (docs/"bevel.html").write_text(bevel,encoding="utf-8")
    (docs/"bevel-copy.html").write_text(bevel,encoding="utf-8")
    (docs/"notes.md").write_text("# Notes\n\nOption: inspect evaluated geometry.\n",encoding="utf-8")
    crawl=crawl_local_documents([docs/"index.html"],approved_roots=[docs],creator="Project fixture",trust_tier="A",version="fixture-1",topics=["modeling"],max_pages=10)
    limited=crawl_local_documents([docs/"index.html"],approved_roots=[docs],creator="Project fixture",trust_tier="A",version="fixture-1",topics=["modeling"],max_pages=1)

    log_paths=sorted((ROOT/"runs").rglob("decision_log.jsonl"))
    mined=mine_session_events(read_decision_logs(log_paths))
    bevel_candidate=next(item for item in mined["candidates"] if "bevel_edges" in item["operation"])
    replay=apply_replay_result(bevel_candidate,{
        "replay_id":"expanded-typed-bevel-cube",
        "different_asset":True,
        "expected":"closed clean beveled mesh with new persistent geometry",
        "observed":"32v/60e/30f, independently clean; operation reported 32/60/30 new elements",
        "pass":True,
        "evidence_path":"runs/2026-08-10_expanded-typed-ops/verify_reports/Typed_Bevel_20260810T164906Z.json",
    })
    assertions={
        "crawl_completed":crawl["completion"]["complete"] and crawl["completion"]["stopped_reason"]=="QUEUE_EXHAUSTED",
        "content_deduplicated":any(item["reason"]=="DUPLICATE_CONTENT" for item in crawl["skipped"]),
        "headings_parameters_warnings_extracted":any(doc["headings"] and doc["operator_parameters"] and doc["warnings"] for doc in crawl["documents"]),
        "max_page_stop_visible":not limited["completion"]["complete"] and limited["completion"]["stopped_reason"]=="MAX_PAGES_REACHED",
        "real_logs_mined":mined["event_count"]==165 and len(log_paths)==5,
        "no_automatic_promotion":not mined["promoted"] and all(item["status"]=="CANDIDATE_REQUIRES_REPLAY" for item in mined["candidates"]),
        "different_asset_replay_validates":replay["status"]=="REPLAY_VALIDATED",
    }
    report={"lab":"documentation_crawl_and_guarded_session_learning","crawl":crawl,"limited_crawl":limited,"log_paths":[str(path.relative_to(ROOT)) for path in log_paths],"mined":mined,"bevel_replay":replay,"assertions":assertions,"pass":all(assertions.values())}
    (out/"learning_system_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"events":mined["event_count"],"candidates":len(mined["candidates"]),"crawl_documents":crawl["completion"]["unique_documents"],"assertions":assertions,"pass":report["pass"]},indent=2))
    if not report["pass"]: raise SystemExit(2)


if __name__=="__main__": main()
