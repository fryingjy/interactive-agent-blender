"""Fresh-process editable-source audit for the Matteo sword candidate."""
from __future__ import annotations
import json
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'runs'/'2026-08-16_matteo-sword-interpretation'
def main():
 bpy.ops.wm.open_mainfile(filepath=str(RUN/'matteo_sword_interpretation.blend'))
 high=bpy.data.collections.get('HIGH_POLY');low=bpy.data.collections.get('LOW_POLY');hs=[o for o in high.objects if o.type=='MESH'] if high else [];ls=[o for o in low.objects if o.type=='MESH'] if low else []
 pairs=[(bpy.data.objects.get('High_'+suffix),bpy.data.objects.get('Low_'+suffix)) for suffix in ('Blade','FanGuard','LeftWing','RightWing','WrappedGrip','Pommel')]
 script=(ROOT/'tools'/'build_matteo_sword_interpretation.py').read_text(encoding='utf8')
 checks={'high_collection_exists':high is not None,'low_collection_exists':low is not None,'expected_component_count':len(hs)==6 and len(ls)==6,'independent_variant_meshes':all(a and b and a.data!=b.data for a,b in pairs),'live_modifiers':all(o.modifiers and all(m.show_viewport and m.show_render for m in o.modifiers) for o in hs+ls),'uv_layers_present':all(o.data.uv_layers for o in hs+ls),'material_assigned':all(o.data.materials for o in hs+ls),'no_modifier_apply_in_builder':'bpy.ops.object.modifier_apply' not in script}
 result={'pass':all(checks.values()),'checks':checks,'boundary':'Technical source audit only; it does not evaluate likeness, depth correctness, material quality, or authored retopology.'};(RUN/'fresh_source_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
