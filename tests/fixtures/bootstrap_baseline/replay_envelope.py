"""Annotation-assisted envelope diagnostic, NOT a complete housing model.

Only 2D drawing ROIs/cameras are authored here. Geometry comes exclusively from
the unchanged registered-mask initializer and competing-family fitter.
Section interiors are deliberately excluded from an OUTER_ENVELOPE diagnostic;
this cannot pass cavity, component, editability or professional-surface review.
"""
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from knowledge_engine.reference_analysis import ReferenceSet, ReferenceItem, PropertyClaim, audit_reference_set
from knowledge_engine.reference_registration import evaluate_reference_registration
from modeling_core.reference_evidence import extract_reference_evidence
from modeling_core.component_evidence import extract_component_evidence
from modeling_core.reference_bundle import build_multiview_evidence_bundle
from modeling_core.initialization import initialize_component_candidates
from modeling_core.component_fitting import fit_component_families
from modeling_core.mesh import build_shape_mesh
from modeling_core.render import render_silhouette

lab = ROOT / 'work/bootstrap-baseline-lab'
out = lab / 'housing-envelope'
out.mkdir(exist_ok=True)
def write(name, value):
    (out / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

freeze = json.loads((ROOT / 'knowledge/foundation/bootstrap_baseline_manifest.json').read_text())
assert digest(ROOT / freeze['curriculum_path']) == freeze['curriculum_sha256'], 'Curriculum changed; label this as an intervention'
sources = json.loads(Path(__file__).with_name('sources.json').read_text())
pdf = lab / 'references/1590A.pdf'
assert digest(pdf) == next(s['sha256'] for s in sources if s['file'] == '1590A.pdf')
import pypdfium2
pdf_document = pypdfium2.PdfDocument(str(pdf))
pdf_document[0].render(scale=2).to_pil().save(lab / 'references/1590A.png')
source = lab / 'references/1590A.png'
image = cv2.imread(str(source))
target = 'B0_HOUSING_OUTER_ENVELOPE_DIAGNOSTIC'
# World X = long dimension; Z = short width; Y = enclosure height.
# Both drawing views share the 2x PDF raster scale. 351px / 92.60mm.
annotations = {'front': [123, 182, 474, 329], 'side': [731, 182, 850, 329]}
write('annotation-contract.json', {
    'source_pdf_sha256': digest(lab / 'references/1590A.pdf'),
    'source_raster_sha256': digest(source), 'rois_xyxy': annotations,
    'pixels_per_mm': 351 / 92.60, 'world_unit_mm': 100,
    'annotation_author': 'agent visual inspection of manufacturer drawing',
    'scope': 'assembled exterior envelope only; not source component labels or cavity geometry',
    'not_automatic_reference_understanding': True,
    'observed': ['TOP VIEW and SECTION A-A END VIEW share short-width axis', '92.60 x 38.50 x 31.00 mm outer dimensions', 'section drawing and exploded photo show a cavity and separate lid'],
    'rejected_interpretation': 'A solid single block or an uncapped side cage is not a complete enclosure',
    'predicted': 'Envelope-only families may fit silhouettes while failing cavity/component/surface channels',
})
items, specs, registration_views = [], [], []
for view_id, (x0,y0,x1,y1) in annotations.items():
    crop = image[y0:y1, x0:x1]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    lines = (gray < 160).astype(np.uint8)
    contours,_ = cv2.findContours(lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(lines)
    cv2.drawContours(filled, [max(contours,key=cv2.contourArea)], -1, 255, -1)
    h,w = gray.shape
    offset_x,offset_y = (512-w)//2,(512-h)//2
    canvas = np.full((512,512,3),255,np.uint8)
    mask = np.zeros((512,512),np.uint8)
    canvas[offset_y:offset_y+h,offset_x:offset_x+w] = crop
    mask[offset_y:offset_y+h,offset_x:offset_x+w] = filled
    crop_path, mask_path = out / f'{view_id}.png', out / f'{view_id}-mask.png'
    cv2.imwrite(str(crop_path),canvas)
    cv2.imwrite(str(mask_path),mask)
    evidence = extract_reference_evidence(crop_path,out / view_id,mask_override=mask_path)
    assert evidence['accepted_for_fitting'], evidence['issues']
    labels_path = out / f'{view_id}-labels.png'
    cv2.imwrite(str(labels_path),(mask>0).astype(np.uint8))
    components = extract_component_evidence(evidence,labels_path,[{'id':'envelope','label':1}])
    write(f'{view_id}-components.json',components)
    items.append(ReferenceItem(
        reference_id=view_id,source_id='hammond-1590a-drawing',target_id=target,target_variant='1590A-envelope-only',
        purposes=('PRIMARY_FORM','DIMENSION','ORTHOGRAPHIC'),view=view_id,projection='ORTHOGRAPHIC',source_tier='VERY_HIGH',
        source_url='https://www.hammfg.com/pdf/1590A.pdf',local_file=str(crop_path),local_sha256=digest(crop_path),
        claims=(PropertyClaim('exterior_envelope','PRIMARY_FORM','Annotated outer boundary of the manufacturer drawing; excludes internal section lines','HIGH'),),
        dimensional_anchors=('92.60 x 38.50 x 31.00 mm',),
        limitations=('Different views from one drawing, not independent sources','Envelope diagnostic does not model enclosure cavity or components'),
    ))
    registration_views.append({'view_id':view_id,'classification':'ORTHOGRAPHIC_OR_NEAR_ORTHOGRAPHIC','alignment_mode':'STRICT_FRAME','projection_evidence':'Labeled orthogonal views in manufacturer engineering drawing; shared raster scale','requested_geometry_claims':['exterior_envelope']})
    specs.append({'view_id':view_id,'source_id':'hammond-1590a-drawing','evidence':evidence,'components':components,
        'solver_view':{'id':view_id,'projection':'orthographic','image_size':[512,512],'yaw_degrees':0.0 if view_id=='front' else 90.0,'pitch_degrees':0.0,'roll_degrees':0.0,'world_scale':512/(351/92.60)/100,'offset_x':0.0,'offset_y':0.0}})
audit = audit_reference_set(ReferenceSet(target,'1590A-envelope-only',tuple(items),('front','side'),('exterior_envelope',),orthographic_required_views=('front','side'),require_dimensional_anchor=True,minimum_full_object_geometry_views=2,minimum_distinct_viewpoint_families=2))
registration = evaluate_reference_registration({'schema_version':1,'target_id':target,'views':registration_views})
write('audit.json',audit); write('registration.json',registration)
bundle = build_multiview_evidence_bundle(audit,registration,specs,required_component_support={'envelope':2})
write('bundle.json',bundle)
assert bundle['accepted_for_shape_solving'],bundle['issues']
assembly = {'schema_version':1,'record_type':'ASSEMBLY_HYPOTHESIS_SET','target_id':target,'target_variant':'1590A-envelope-only','components':[{'component_id':'envelope','representation_candidates':[{'family':'section_loft'},{'family':'profile_extrusion'}]}],'relationship_hypotheses':[]}
write('assembly.json',assembly)
initialized = initialize_component_candidates(bundle,assembly)
write('initialized.json',initialized)
assert initialized['ready_for_component_fitting'],initialized['initialization_reports']
print('References frozen and candidates initialized; fitting unchanged defaults.',flush=True)
selected = fit_component_families(bundle,assembly,initialized['components'],seed=0,maxiter=20)
write('selection.json',selected)
for candidate in selected['components']['envelope']['selection']['candidates']:
    result = candidate['result']
    if result is None: continue
    verts,faces = build_shape_mesh(result['hypothesis']['shape'])
    for view in result['hypothesis']['views']:
        for authored in (False,True):
            rendered = render_silhouette(verts,faces,view,fill_open_boundaries=not authored)
            cv2.imwrite(str(out / f"{candidate['family']}-{view['id']}-{'authored' if authored else 'volume'}.png"),rendered.astype(np.uint8)*255)
    print(candidate['family'],candidate['mean_view_loss'],candidate['compatible'],flush=True)
print('ready_for_compilation',selected['ready_for_compilation'],flush=True)
