"""Fixed-policy negative-space experiment; never authorizes geometry."""
import json
import hashlib
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'work/bootstrap-mask-intervention-lab'
OUT.mkdir(parents=True, exist_ok=True)
import sys
sys.path.insert(0, str(ROOT))
from modeling_core.reference_evidence import analyze_reference_mask, extract_reference_evidence
frozen_sources = {r['file']: r['sha256'] for r in json.loads(Path(__file__).with_name('sources.json').read_text())}
names = ['housing-2', 'knob-gray', 'clip-front', 'clip-alt']
rows = []
for name in names:
    path = ROOT / 'work/bootstrap-baseline-lab/extraction' / name / 'reference_mask.png'
    source = ROOT / 'work/bootstrap-baseline-lab/references' / f'{name}.jpg'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == frozen_sources[source.name]
    baseline = json.loads(path.with_name('reference_evidence.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == baseline['artifact_sha256']['editable_mask']
    mask = cv2.imread(str(path),0) > 0
    inventory = analyze_reference_mask(mask)
    (OUT / f'{name}-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    n, labels, stats, _ = cv2.connectedComponentsWithStats((~mask).astype(np.uint8),8)
    border = set(labels[0]) | set(labels[-1]) | set(labels[:,0]) | set(labels[:,-1])
    ids = [i for i in range(1,n) if i not in border]
    yy,xx = np.where(mask)
    # Frozen before reading hole areas; this is a tested prior, not semantics.
    limit = max(4, round(0.0002 * (xx.max()-xx.min()+1)*(yy.max()-yy.min()+1)))
    small = [i for i in ids if stats[i,cv2.CC_STAT_AREA] <= limit]
    candidate = mask | np.isin(labels,small)
    cv2.imwrite(str(OUT / f'{name}-candidate.png'),candidate.astype(np.uint8)*255)
    overlay = cv2.imread(str(ROOT / 'work/bootstrap-baseline-lab/references' / f'{name}.jpg'))
    overlay[candidate & ~mask] = (0,0,255)
    cv2.imwrite(str(OUT / f'{name}-changes.png'),overlay)
    rows.append({'source_mask_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'name':name,'cutoff_px':int(limit),'before':len(ids),'after':len(ids)-len(small),'changed_pixels':int((candidate != mask).sum()),'retained':[{'id':i,'area':int(stats[i,4]),'bbox_xywh':[int(x) for x in stats[i,:4]]} for i in ids if i not in small]})
    # Separate source-reviewed intervention, not the size-only policy above.
    # These two inspected *assembled views* show a backed surface at all image
    # gaps. This decision does NOT extend to an open housing or underside view.
    if name in {'housing-2','knob-gray'}:
        reviewed = mask | np.isin(labels,ids)
        override = OUT / f'{name}-reviewed.png'
        cv2.imwrite(str(override),reviewed.astype(np.uint8)*255)
        evidence = extract_reference_evidence(source, OUT / f'{name}-reviewed-evidence', mask_override=override)
        assert evidence['measurements']['enclosed_negative_space_count'] == 0
        assert evidence['measurements']['bbox_pixels'] == inventory['bbox_pixels']
        exterior = np.isin(labels, list(border))
        assert np.array_equal(reviewed[exterior], mask[exterior])
        overlay = cv2.imread(str(source))
        overlay[reviewed & ~mask] = (0,0,255)
        cv2.imwrite(str(OUT / f'{name}-reviewed-changes.png'),overlay)
        rows[-1]['source_reviewed_override'] = {'after':0,'changed_pixels':int((reviewed != mask).sum()),'source_sha256':frozen_sources[source.name],'override_sha256':evidence['extraction']['override_sha256'],'evidence_sha256':hashlib.sha256((OUT / f'{name}-reviewed-evidence/reference_evidence.json').read_bytes()).hexdigest(),'decision':'Enclosed bright gaps lie on backed solid surfaces in this assembled view; fill only enclosed background, retain all external boundaries.','reviewer':'agent source-image review; no independent approval','geometry_authorized':False}
    else:
        rows[-1]['source_reviewed_override'] = {'decision':'DEFER: preserve ambiguous small gaps and wire loops; area alone cannot select real negative space.','geometry_authorized':False}

# Explicit counterexample: size filtering destroys a genuine one-pixel aperture.
tiny = np.ones((20,20),bool)
tiny[10,10] = False
n, tiny_labels, tiny_stats, _ = cv2.connectedComponentsWithStats((~tiny).astype(np.uint8), connectivity=8)
tiny_after = tiny | np.isin(tiny_labels, [i for i in range(1,n) if tiny_stats[i,4] <= 4])
before_count = analyze_reference_mask(tiny)['enclosed_negative_space_count']
after_count = analyze_reference_mask(tiny_after)['enclosed_negative_space_count']
assert (before_count, after_count) == (1,0)
rows.append({'counterexample':'Known tiny true aperture inside a solid silhouette','hole_area':1,'fixed_minimum_cutoff':4,'measured_before':before_count,'measured_after':after_count,'size_only_policy_erases_real_hole':after_count < before_count,'policy_accepted_for_automatic_use':False})
(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,indent=2))
