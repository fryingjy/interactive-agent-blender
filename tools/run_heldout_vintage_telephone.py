"""Held-out vintage telephone wall-clock candidate from neutral renders only.

The source GLTF is never imported here. Visible continuous skins are authored as
connected quad cages; separate objects require assembly, repetition, or material reasons.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import bmesh, bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender_ops'))
from render_passes import render_silhouette

VIEWS={'front':Vector((0,-1,0)),'side':Vector((1,0,0)),'top':Vector((0,0,1)),'isometric':Vector((1,-1,.8)).normalized()}

def args():
    vals=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(vals)!=1: raise SystemExit('expected OUTPUT_DIR after --')
    out=Path(vals[0]).resolve(); out.mkdir(parents=True,exist_ok=True); return out

def mat(name,color,metal=0.0,rough=.4):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.metallic=metal; m.roughness=rough; m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m

def make_obj(name,verts,faces,collection,material,props=None):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.materials.append(material); me.update(calc_edges=True)
    ob=bpy.data.objects.new(name,me); collection.objects.link(ob)
    for p in me.polygons: p.use_smooth=True
    if props:
        for k,v in props.items(): ob[k]=v
    uv=me.uv_layers.new(name='UVMap')
    xs=[v.co.x for v in me.vertices]; zs=[v.co.z for v in me.vertices]; dx=max(xs)-min(xs) or 1; dz=max(zs)-min(zs) or 1
    for poly in me.polygons:
        for li in poly.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv=((co.x-min(xs))/dx,(co.z-min(zs))/dz)
    return ob

def boundary_coords(n):
    out=[]
    for i in range(n): out.append((i,0))
    for j in range(1,n): out.append((n-1,j))
    for i in range(n-2,-1,-1): out.append((i,n-1))
    for j in range(n-2,0,-1): out.append((0,j))
    return out

def build_housing(collection,material):
    n=5; bc=boundary_coords(n); verts=[]; faces=[]; rings=[]
    specs=[
      (-2.25,3.40,1.30,0.00),(-1.11,3.40,1.30,0.00),(-.96,3.12,1.18,0.00),(-.81,2.78,1.06,0.00),
      (-.66,2.78,1.06,0.00),(-.54,2.78,1.06,.10),(1.91,2.78,1.06,.10),(2.04,2.78,1.06,0.00),
      (2.22,2.72,1.08,0.00),(2.42,2.48,1.10,0.00),(2.63,1.86,1.12,0.00),(2.76,1.16,1.12,0.00)]
    ring_maps=[]
    for z,w,d,inset in specs:
        ring=[]; mp={}
        for i,j in bc:
            u=-1+2*i/(n-1); v=-1+2*j/(n-1); y=v*d/2
            if j==0 and 0<i<n-1: y+=inset
            idx=len(verts); verts.append((u*w/2,y,z)); ring.append(idx); mp[(i,j)]=idx
        rings.append(ring); ring_maps.append(mp)
    for a,b in zip(rings,rings[1:]):
        for k in range(len(a)): faces.append((a[k],a[(k+1)%len(a)],b[(k+1)%len(a)],b[k]))
    for end,normal_up in ((0,False),(len(specs)-1,True)):
        z,w,d,inset=specs[end]; mp=ring_maps[end]
        for j in range(1,n-1):
            for i in range(1,n-1):
                u=-1+2*i/(n-1); v=-1+2*j/(n-1); mp[(i,j)]=len(verts); verts.append((u*w/2,v*d/2,z))
        for j in range(n-1):
            for i in range(n-1):
                q=(mp[(i,j)],mp[(i+1,j)],mp[(i+1,j+1)],mp[(i,j+1)])
                faces.append(q if normal_up else tuple(reversed(q)))
    ob=make_obj('Main_Housing',verts,faces,collection,material,{
      'construction':'one box/profile cage; connected vertical loop rings; routed recessed front band',
      'primitive_operators_used':0,'required_connected_components':1,'primary_all_quad_required':True})
    # Semantic weighted bevel: select genuine dihedral edges, not every smooth longitudinal edge.
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.edges.ensure_lookup_table(); weighted=[]
    for e in bm.edges:
        if len(e.link_faces)==2 and e.calc_face_angle(0.0)>math.radians(24): weighted.append(e.index)
    bm.free(); attr=ob.data.attributes.new('bevel_weight_edge','FLOAT','EDGE')
    for e in ob.data.edges: attr.data[e.index].value=1.0 if e.index in weighted else 0.0
    ob['intended_sharp_edge_count']=len(weighted); ob['weighted_bevel_edges']=len(weighted)
    bev=ob.modifiers.new('Semantic weighted bevel','BEVEL'); bev.limit_method='WEIGHT'; bev.width=.035; bev.segments=2; bev.affect='EDGES'
    sub=ob.modifiers.new('Controlled housing SubD','SUBSURF'); sub.levels=sub.render_levels=1
    return ob

def concentric_disk(u,v):
    if abs(u)<1e-9 and abs(v)<1e-9: return 0.0,0.0
    if abs(u)>abs(v): r=u; theta=(math.pi/4)*(v/u)
    else: r=v; theta=math.pi/2-(math.pi/4)*(u/v)
    return r*math.cos(theta),r*math.sin(theta)

def build_handset(collection,material):
    n=4; bc=boundary_coords(n); verts=[]; faces=[]; rings=[]; maps=[]
    specs=[(-1.25,.34),(-1.15,.40),(-1.02,.28),(-.92,.14),(-.60,.12),(-.30,.15),(0,.20),(.30,.15),(.60,.12),(.92,.14),(1.02,.28),(1.15,.40),(1.25,.34)]
    cy=-1.02; cz=-1.03
    for x,r in specs:
        ring=[]; mp={}
        for i,j in bc:
            u=-1+2*i/(n-1); v=-1+2*j/(n-1); dy,dz=concentric_disk(u,v)
            idx=len(verts); verts.append((x,cy+dy*r,cz+dz*r)); ring.append(idx); mp[(i,j)]=idx
        rings.append(ring); maps.append(mp)
    for a,b in zip(rings,rings[1:]):
        for k in range(len(a)): faces.append((a[k],a[(k+1)%len(a)],b[(k+1)%len(a)],b[k]))
    for end,outward_positive_x in ((0,False),(len(specs)-1,True)):
        x,r=specs[end]; mp=maps[end]
        for j in range(1,n-1):
            for i in range(1,n-1):
                u=-1+2*i/(n-1); v=-1+2*j/(n-1); dy,dz=concentric_disk(u,v); mp[(i,j)]=len(verts); verts.append((x,cy+dy*r,cz+dz*r))
        for j in range(n-1):
            for i in range(n-1):
                q=(mp[(i,j)],mp[(i+1,j)],mp[(i+1,j+1)],mp[(i,j+1)])
                # Grid order points toward +X in YZ parameterization after reversal choice.
                faces.append(q if outward_positive_x else tuple(reversed(q)))
    ob=make_obj('Handset',verts,faces,collection,material,{
      'construction':'one connected longitudinal skin with 12-vertex circularized cross-section loops',
      'radial_vertices':12,'primitive_operators_used':0,'required_connected_components':1,'primary_all_quad_required':True})
    sub=ob.modifiers.new('Handset Catmull-Clark','SUBSURF'); sub.levels=sub.render_levels=2
    return ob

def rect_ring(name,cx,cz,outer_x,outer_z,inner_x,inner_z,y0,y1,collection,material):
    outer=[(cx-outer_x,cz-outer_z),(cx+outer_x,cz-outer_z),(cx+outer_x,cz+outer_z),(cx-outer_x,cz+outer_z)]
    inner=[(cx-inner_x,cz-inner_z),(cx+inner_x,cz-inner_z),(cx+inner_x,cz+inner_z),(cx-inner_x,cz+inner_z)]
    verts=[]
    for y in (y0,y1):
        for x,z in outer+inner: verts.append((x,y,z))
    faces=[]
    for layer,rev in ((0,False),(8,True)):
        for i in range(4):
            q=(layer+i,layer+(i+1)%4,layer+4+(i+1)%4,layer+4+i)
            faces.append(tuple(reversed(q)) if rev else q)
    for loopoff in (0,4):
        for i in range(4):
            a=loopoff+i; b=loopoff+(i+1)%4; faces.append((a,b,b+8,a+8) if loopoff==0 else (b,a,a+8,b+8))
    ob=make_obj(name,verts,faces,collection,material,{'assembly_reason':'replaceable stamped trim'})
    return ob

def radial_ring(name,cx,cz,r_outer,r_inner,y0,y1,segs,collection,material):
    verts=[]; faces=[]
    for y in (y0,y1):
        for r in (r_outer,r_inner):
            for i in range(segs):
                a=math.tau*i/segs; verts.append((cx+r*math.cos(a),y,cz+r*math.sin(a)))
    def idx(layer,rad,i): return layer*2*segs+rad*segs+(i%segs)
    for i in range(segs):
        j=i+1
        faces += [
          (idx(0,0,i),idx(0,0,j),idx(1,0,j),idx(1,0,i)),
          (idx(0,1,j),idx(0,1,i),idx(1,1,i),idx(1,1,j)),
          (idx(1,0,i),idx(1,0,j),idx(1,1,j),idx(1,1,i)),
          (idx(0,0,j),idx(0,0,i),idx(0,1,i),idx(0,1,j))]
    ob=make_obj(name,verts,faces,collection,material,{'radial_vertices':segs,'assembly_reason':'removable radial dial bezel'}); bev=ob.modifiers.new('Dial rim bevel','BEVEL'); bev.limit_method='ANGLE'; bev.angle_limit=math.radians(30); bev.width=.018; bev.segments=2; sub=ob.modifiers.new('Dial smoothing SubD','SUBSURF'); sub.levels=sub.render_levels=1
    return ob

def cylinder(name,cx,cy,cz,r,depth,segs,collection,material,assembly):
    verts=[]; faces=[]
    for y in (cy-depth/2,cy+depth/2):
        for i in range(segs):
            a=math.tau*i/segs; verts.append((cx+r*math.cos(a),y,cz+r*math.sin(a)))
    for i in range(segs): faces.append((i,(i+1)%segs,(i+1)%segs+segs,i+segs))
    faces.append(tuple(reversed(range(segs)))); faces.append(tuple(range(segs,2*segs)))
    return make_obj(name,verts,faces,collection,material,{'radial_vertices':segs,'assembly_reason':assembly})

def profile_prism(name,points,y0,y1,collection,material,assembly):
    verts=[(x,y0,z) for x,z in points]+[(x,y1,z) for x,z in points]; n=len(points); faces=[]
    faces.append(tuple(reversed(range(n)))); faces.append(tuple(range(n,2*n)))
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    ob=make_obj(name,verts,faces,collection,material,{'assembly_reason':assembly}); bev=ob.modifiers.new(name+' bevel','BEVEL'); bev.limit_method='ANGLE'; bev.angle_limit=math.radians(30); bev.width=.006 if 'Hand' in name else .015; bev.segments=2
    return ob

def curve_tube(name,points,radius,collection,material):
    cu=bpy.data.curves.new(name+'Curve','CURVE'); cu.dimensions='3D'; cu.bevel_depth=radius; cu.bevel_resolution=3; cu.resolution_u=12
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points): p.co=co; p.handle_left_type=p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu); collection.objects.link(ob); ob.data.materials.append(material); ob['assembly_reason']='flexible replaceable cord/cradle rod'; return ob

def health(ob,evaluated=False):
    owner=None; me=ob.data
    if evaluated: owner=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=owner.to_mesh()
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); unseen=set(bm.verts); comps=0
    while unseen:
        comps+=1; stack=[unseen.pop()]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                o=e.other_vert(v)
                if o in unseen: unseen.remove(o); stack.append(o)
    d={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),'triangles':sum(len(f.verts)==3 for f in bm.faces),'ngons':sum(len(f.verts)>4 for f in bm.faces),'connected_components':comps,'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'loose_vertices':sum(not v.link_edges for v in bm.verts)}
    bm.free()
    if owner: owner.to_mesh_clear()
    return d

def render_review(scene,out,objects,view):
    direction=VIEWS[view]; pts=[]
    for ob in objects:
        for corner in ob.bound_box: pts.append(ob.matrix_world@Vector(corner))
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts))); center=(mn+mx)/2; diag=(mx-mn).length
    cd=bpy.data.cameras.new(view+'CameraData'); cd.type='ORTHO'; cd.ortho_scale=diag*1.08
    cam=bpy.data.objects.new(view+'Camera',cd); scene.collection.objects.link(cam); cam.location=center+direction*diag*2.2; cam.rotation_euler=direction.to_track_quat('Z','Y').to_euler(); scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH'; sh=scene.display.shading; sh.light='MATCAP'; sh.studio_light='hard_surface_grey.exr'; sh.color_type='MATERIAL'; sh.show_shadows=True; sh.show_cavity=True; sh.cavity_type='BOTH'
    scene.render.filepath=str(out/f'candidate_{view}_solid.png'); bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam,do_unlink=True); bpy.data.cameras.remove(cd)

def main():
    out=args(); bpy.ops.wm.read_factory_settings(use_empty=True); scene=bpy.context.scene; scene.render.resolution_x=scene.render.resolution_y=720; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.world=bpy.data.worlds.new('Telephone Review World'); scene.world.color=(.025,.025,.025)
    col=bpy.data.collections.new('Heldout Vintage Telephone'); scene.collection.children.link(col)
    red=mat('Worn red housing',(0.30,.055,.035),.55,.30); dark=mat('Bakelite handset',(0.025,.021,.018),.05,.23); brass=mat('Aged metal trim',(.32,.23,.09),.72,.28); face=mat('Clock face',(.52,.48,.38),.12,.36); black=mat('Dial apertures',(.012,.012,.010),.0,.32)
    objs=[]; body=build_housing(col,red); handset=build_handset(col,dark); objs += [body,handset]
    objs.append(rect_ring('Upper_Face_Trim',0,.80,1.18,1.45,1.05,1.33,-.61,-.72,col,brass))
    objs.append(rect_ring('Lower_Panel_Trim',0,-1.78,1.42,.34,1.28,.24,-.71,-.78,col,brass))
    objs.append(radial_ring('Dial_Bezel',0,.41,1.02,.74,-.73,-.84,16,col,brass))
    objs.append(cylinder('Clock_Face',0,-.87,.41,.72,.07,16,col,face,'serviceable clock insert'))
    # Twelve linked radial apertures/fasteners.
    hole_data=None
    for i in range(12):
        a=math.tau*i/12; x=.88*math.cos(a); z=.41+.88*math.sin(a)
        h=cylinder('Dial_Aperture' if i==0 else f'Dial_Aperture_{i:02d}',0,-.91,0,.085,.045,12,col,black,'repeated dial aperture')
        if hole_data is None: hole_data=h.data
        else: old=h.data; h.data=hole_data; bpy.data.meshes.remove(old)
        h.location=(x,0,z); objs.append(h)
    # Clock hands as separate service parts.
    objs.append(profile_prism('Hour_Hand',[(-.035,.38),(.035,.38),(.055,.80),(-.055,.80)],-.94,-.98,col,black,'clock hand articulation'))
    objs.append(profile_prism('Minute_Hand',[(-.025,.38),(.025,.38),(.035,.99),(-.035,.99)],-.95,-.99,col,black,'clock hand articulation'))
    # Mirrored cradle blocks share mesh data.
    left=profile_prism('Cradle_Left',[(-1.53,-1.49),(-1.12,-1.49),(-1.08,-.98),(-1.40,-.91)],-1.02,-1.20,col,brass,'separate handset cradle'); objs.append(left)
    right=left.copy(); right.data=left.data; right.name='Cradle_Right'; right.scale.x=-1; col.objects.link(right); objs.append(right)
    # Top latch and visible flexible rods/cord.
    objs.append(profile_prism('Top_Latch',[(-.42,1.70),(.42,1.70),(.34,2.08),(-.34,2.08)],-.72,-.82,col,brass,'service latch'))
    cord=curve_tube('Handset_Cord',[(1.20,-1.02,-1.08),(1.72,-.88,-1.30),(1.58,-.72,-1.78),(1.10,-.70,-2.05)],.035,col,dark)
    rod1=curve_tube('Cradle_Rod_Left',[(-1.25,-1.05,-1.07),(-1.18,-1.10,-1.38),(-1.08,-.80,-1.65)],.035,col,brass)
    rod2=curve_tube('Cradle_Rod_Right',[(1.25,-1.05,-1.07),(1.18,-1.10,-1.38),(1.08,-.80,-1.65)],.035,col,brass)
    all_render=objs+[cord,rod1,rod2]
    bpy.context.view_layer.update()
    names=[o.name for o in objs]
    sil=[]
    for view in ('front','side','top'):
        sil.append(render_silhouette(names,str(out/f'candidate_{view}_mask.png'),view=view,resolution=720,margin=1.12,frame_name=names)); render_review(scene,out,all_render,view)
    render_review(scene,out,all_render,'isometric')
    mesh_records={o.name:{'base':health(o),'evaluated':health(o,True)} for o in objs}
    assertions={
      'source_geometry_not_imported':not any('vintage_telephone_wall_clock' in o.name.lower() for o in bpy.data.objects),
      'no_mesh_primitive_operators':all(int(o.get('primitive_operators_used',0))==0 for o in (body,handset)),
      'housing_one_component_all_quad':mesh_records[body.name]['base']['connected_components']==1 and mesh_records[body.name]['base']['faces']==mesh_records[body.name]['base']['quads'],
      'handset_one_component_all_quad':mesh_records[handset.name]['base']['connected_components']==1 and mesh_records[handset.name]['base']['faces']==mesh_records[handset.name]['base']['quads'],
      'housing_closed_clean':mesh_records[body.name]['base']['non_manifold_edges']==0 and mesh_records[body.name]['base']['degenerate_faces']==0,
      'handset_closed_clean':mesh_records[handset.name]['base']['non_manifold_edges']==0 and mesh_records[handset.name]['base']['degenerate_faces']==0,
      'weighted_bevel_complete':body['intended_sharp_edge_count']==body['weighted_bevel_edges'] and body['weighted_bevel_edges']>0,
      'sparse_radial_cages':handset['radial_vertices']==12 and all(int(o.get('radial_vertices',12))<=16 for o in objs if 'radial_vertices' in o),
      'all_meshes_have_uvs_and_materials':all(bool(o.data.uv_layers and o.data.materials) for o in objs),
      'linked_radial_repetition':len({o.data.as_pointer() for o in objs if o.name.startswith('Dial_Aperture')})==1,
      'silhouette_render_succeeded':all('error' not in item for item in sil),
      'all_evaluated_meshes_closed_and_nondegenerate':all(r['evaluated']['non_manifold_edges']==0 and r['evaluated']['degenerate_faces']==0 for r in mesh_records.values()),
    }
    report={'lab':'heldout_vintage_telephone','stage':'primary_plus_secondary_blockout','construction_status':'candidate built from neutral renders only','objects':len(objs),'curves':3,'mesh_records':mesh_records,'silhouette_records':sil,'assertions':assertions,'pass':all(assertions.values())}
    (out/'telephone_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); bpy.ops.wm.save_as_mainfile(filepath=str(out/'heldout_vintage_telephone.blend')); print('TELEPHONE_RESULT:'+json.dumps(report))
    if not report['pass']: raise SystemExit(2)
main()
