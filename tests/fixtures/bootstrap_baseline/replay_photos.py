"""Manual networked B0 replay; never imported by the automated test suite.

This is experiment support, not another modeling CLI. It downloads only the
frozen manufacturer references, verifies their hashes, and calls the existing
extractor/proposer unchanged. It never creates Blender geometry.
"""
import hashlib
import json
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from modeling_core.reference_evidence import extract_reference_evidence
from modeling_core.component_proposals import propose_component_regions


def main():
    lab = ROOT / 'work/bootstrap-baseline-lab'
    references = lab / 'references'
    references.mkdir(parents=True, exist_ok=True)
    freeze = json.loads((ROOT / 'knowledge/foundation/bootstrap_baseline_manifest.json').read_text())
    actual = hashlib.sha256((ROOT / freeze['curriculum_path']).read_bytes()).hexdigest()
    if actual != freeze['curriculum_sha256']:
        raise ValueError('Curriculum changed: replay the baseline commit or label this as an intervention')
    sources = json.loads(Path(__file__).with_name('sources.json').read_text())
    rows = []
    for source in sources:
        path = references / source['file']
        if path.exists():
            raw = path.read_bytes()
        else:
            response = requests.get(source['url'], timeout=45)
            response.raise_for_status()
            raw = response.content
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError(f"Frozen source changed: {source['file']}; do not silently replace it")
        if not path.exists():
            path.write_bytes(raw)
        if path.suffix != '.jpg':
            continue
        out = lab / 'extraction' / path.stem
        record = {'source': source}
        try:
            result = extract_reference_evidence(path, out)
            record['extraction'] = result
            if result['accepted_for_fitting']:
                record['components'] = propose_component_regions(out / 'reference_evidence.json', out / 'components')
        except Exception as error:
            record['error'] = f'{type(error).__name__}: {error}'
        rows.append(record)
        print(path.name, record.get('extraction', {}).get('accepted_for_fitting'), record.get('error'), flush=True)
    (lab / 'extraction-results.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
