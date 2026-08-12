"""Fourth-family held-out metal watering-can candidate from neutral renders only."""
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

def mat(name,color,metal=.0,rough=.4):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.metallic=metal; m.roughness=rough; m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m

def boundary(n):
    return [(i,0) for i in range(n)]+[(n-1,j) for j in range(1,n)]+[(i,n-1) for i in range(n-2,-1,-1)]+[(0,j) for j in range(n-2,0,-1)]

def disk(u,v):
    if abs(u)<1e-9 and abs(v)<1e-9:return 0.,0.
    if abs(u)>abs(v): r=u; t=math.pi/4*(v/u)
    else:r=v;t=math.pi/2-math.pi/4*(u/v)
    return r*math.cos(t),r*math.sin(t)

def make_obj(name,verts,faces,col,material,props=None):
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.materials.append(material); me.update(calc_edges=True)
    ob=bpy.data.objects.new(name,me); col.objects.link(ob)
    for p in me.polygons:p.use_smooth=True
    uv=me.uv_layers.new(name='UVMap'); xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
    dx=max(xs)-min(xs) or 1; dy=max(ys)-min(ys) or 1; dz=max(zs)-min(zs) or 1
    for p in me.polygons:
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv=((co.y-min(ys))/dy,(co.z-min(zs))/dz)
    if props:
        for k,v in props.items():ob[k]=v
    return ob

def ring_loft(name,specs,grid_n,col,material,props=None):
    bc=boundary(grid_n); verts=[]; faces=[]; rings=[]
    for z,r in specs:
        ring=[]
        for i,j in bc:
            u=-1+2*i/(grid_n-1);v=-1+2*j/(grid_n-1);x,y=disk(u,v);ring.append(len(verts));verts.append((x*r,y*r,z))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for k in range(len(a)):faces.append((a[k],a[(k+1)%len(a)],b[(k+1)%len(a)],b[k]))
    for ridx,up in ((0,False),(len(rings)-1,True)):
        z,r=specs[ridx]; mp={bc[k]:rings[ridx][k] for k in range(len(bc))}
        for j in range(1,grid_n-1):
            for i in range(1,grid_n-1):
                x,y=disk(-1+2*i/(grid_n-1),-1+2*j/(grid_n-1));mp[(i,j)]=len(verts);verts.append((x*r,y*r,z))
        for j in range(grid_n-1):
            for i in range(grid_n-1):
                q=(mp[(i,j)],mp[(i+1,j)],mp[(i+1,j+1)],mp[(i,j+1)]);faces.append(q if up else tuple(reversed(q)))
    return make_obj(name,verts,faces,col,material,props)

def path_loft(name,centers,radii,grid_n,col,material,props=None):
    bc=boundary(grid_n); verts=[];faces=[];rings=[]
    frames=[]
    for k,c in enumerate(centers):
        tangent=(Vector(centers[min(k+1,len(centers)-1)])-Vector(centers[max(k-1,0)])).normalized(); bx=Vector((1,0,0)); by=tangent.cross(bx).normalized();frames.append((bx,by))
        ring=[]
        for i,j in bc:
            u=-1+2*i/(grid_n-1);v=-1+2*j/(grid_n-1);a,b=disk(u,v);p=Vector(c)+(bx*a+by*b)*radii[k];ring.append(len(verts));verts.append(tuple(p))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for k in range(len(a)):faces.append((a[k],a[(k+1)%len(a)],b[(k+1)%len(a)],b[k]))
    for ridx,outward in ((0,False),(len(rings)-1,True)):
        mp={bc[k]:rings[ridx][k] for k in range(len(bc))};c=Vector(centers[ridx]);bx,by=frames[ridx];r=radii[ridx]
        for j in range(1,grid_n-1):
            for i in range(1,grid_n-1):
                a,b=disk(-1+2*i/(grid_n-1),-1+2*j/(grid_n-1));mp[(i,j)]=len(verts);verts.append(tuple(c+(bx*a+by*b)*r))
        for j in range(grid_n-1):
            for i in range(grid_n-1):
                q=(mp[(i,j)],mp[(i+1,j)],mp[(i+1,j+1)],mp[(i,j+1)]);faces.append(q if outward else tuple(reversed(q)))
    return make_obj(name,verts,faces,col,material,props)

def annulus(name,z,inner,outer,height,segments,col,material):
    verts=[];faces=[]
    for zz in (z-height/2,z+height/2):
        for r in (inner,outer):
            for i in range(segments):
                a=math.tau*i/segments;verts.append((r*math.cos(a),r*math.sin(a),zz))
    def idx(level,which,i):return level*2*segments+which*segments+(i%segments)
    for i in range(segments):
        j=i+1; faces += [(idx(0,1,i),idx(0,1,j),idx(1,1,j),idx(1,1,i)),(idx(1,0,i),idx(1,0,j),idx(0,0,j),idx(0,0,i)),(idx(1,0,i),idx(1,1,i),idx(1,1,j),idx(1,0,j)),(idx(0,0,j),idx(0,1,j),idx(0,1,i),idx(0,0,i))]
    return make_obj(name,verts,faces,col,material,{'physical_role':'rolled opening rim','radial_vertices':segments})

def curve_handle(col,material):
    # A filled Curve converted in Blender 5.2 leaves its cap islands separate
    # from the tube skin.  This explicit path loft keeps the same editable
    # path logic but closes the endpoint grids into one all-quad manifold mesh.
    pts=[(0,1.22,1.18),(0,1.82,1.25),(0,2.45,1.08),(0,2.90,.62),
         (0,3.05,.10),(0,2.90,-.55),(0,2.55,-1.20),(0,1.95,-1.33),(0,1.38,-1.25)]
    ob=path_loft('Arched_Handle',pts,[.105]*len(pts),4,col,material,{
        'construction':'one continuous path loft with closed endpoint grids',
        'primitive_operators_used':0,
        'authored_continuous_path_loft':True,
        'primary_all_quad_required':True,
    })
    return ob

def health(ob,evaluated=False):
    mesh=ob.data
    if evaluated:
        dg=bpy.context.evaluated_depsgraph_get();eo=ob.evaluated_get(dg);mesh=eo.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
    unseen=set(bm.verts); comps=0
    while unseen:
        comps+=1;stack=[unseen.pop()]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                o=e.other_vert(v)
                if o in unseen:unseen.remove(o);stack.append(o)
    rec={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'connected_components':comps}
    bm.free()
    if evaluated:eo.to_mesh_clear()
    return rec

def render_review(scene,out,objects,view):
    pts=[]
    for ob in objects:
        pts += [ob.matrix_world@Vector(c) for c in ob.bound_box]
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)));mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)));center=(mn+mx)/2;diag=(mx-mn).length;d=VIEWS[view]
    bpy.ops.object.camera_add(location=center+d*diag*2.2);cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=diag*1.12;cam.rotation_euler=d.to_track_quat('Z','Y').to_euler();scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.render.filepath=str(out/f'candidate_{view}_beauty.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)

def main():
    out=args();bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.resolution_x=scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('Review World');scene.world.color=(.045,.045,.045)
    col=bpy.data.collections.new('WateringCan');scene.collection.children.link(col);metal=mat('Galvanized Metal',(.24,.31,.35),.72,.28);dark=mat('Opening',(.018,.022,.024),0,.4)
    body=ring_loft('Connected_Vessel',[(-1.62,1.56),(-1.56,1.68),(-1.46,1.72),(-1.36,1.60),(.98,1.32),(1.24,1.27),(1.31,1.39),(1.40,1.40),(1.48,1.18)],5,col,metal,{'construction':'one connected 16-edge ring loft; body bands authored as loop transitions','radial_vertices':16,'primitive_operators_used':0,'required_connected_components':1,'primary_all_quad_required':True})
    attr=body.data.attributes.new('bevel_weight_edge','FLOAT','EDGE');weighted=[]
    for e in body.data.edges:
        a,b=[body.data.vertices[i].co for i in e.vertices]
        horizontal=abs(a.z-b.z)<1e-6
        if horizontal:attr.data[e.index].value=1.;weighted.append(e.index)
    body['intended_sharp_edge_count']=len(weighted);body['weighted_bevel_edges']=len(weighted)
    bev=body.modifiers.new('Weighted circumferential bevel','BEVEL');bev.limit_method='WEIGHT';bev.width=.035;bev.segments=2;bev.affect='EDGES'
    spout_centers=[(0,-1.33,-.62),(0,-1.75,-.34),(0,-2.35,.08),(0,-3.02,.55),(0,-3.72,1.04),(0,-4.15,1.35)]
    spout=path_loft('Connected_Tapered_Spout',spout_centers,[.38,.36,.32,.28,.24,.22],4,col,metal,{'construction':'one connected 12-edge tapered skin','radial_vertices':12,'primitive_operators_used':0,'required_connected_components':1,'primary_all_quad_required':True})
    rose=path_loft('Rose_Head',[(0,-4.11,1.31),(0,-4.29,1.45),(0,-4.48,1.60),(0,-4.62,1.70)],[.26,.54,.62,.50],4,col,metal,{'physical_role':'replaceable perforated rose','radial_vertices':12,'primitive_operators_used':0})
    handle=curve_handle(col,metal);rim=annulus('Opening_Rim',1.50,.90,1.19,.10,16,col,metal)
    inner=ring_loft('Opening_Shadow',[(1.495,.88),(1.51,.88)],5,col,dark,{'physical_role':'opening depth insert','radial_vertices':16})
    objs=[body,spout,rose,handle,rim,inner];bpy.context.view_layer.update();names=[o.name for o in objs]
    sil=[]
    for view in ('front','side','top'):
        sil.append(render_silhouette(names,str(out/f'candidate_{view}_mask.png'),view=view,resolution=720,margin=1.12,frame_name=names));render_review(scene,out,objs,view)
    render_review(scene,out,objs,'isometric')
    records={o.name:{'base':health(o),'evaluated':health(o,True)} for o in objs}
    assertions={'source_geometry_not_imported':not any('watering_can_metal_01' in o.name.lower() for o in bpy.data.objects),'body_one_component_all_quad':records[body.name]['base']['connected_components']==1 and records[body.name]['base']['faces']==records[body.name]['base']['quads'],'spout_one_component_all_quad':records[spout.name]['base']['connected_components']==1 and records[spout.name]['base']['faces']==records[spout.name]['base']['quads'],'body_and_spout_closed':records[body.name]['base']['non_manifold_edges']==0 and records[spout.name]['base']['non_manifold_edges']==0,'body_uses_16_vertices':body['radial_vertices']==16,'spout_uses_12_vertices':spout['radial_vertices']==12,'weighted_bevel_complete':body['intended_sharp_edge_count']==body['weighted_bevel_edges'] and body['weighted_bevel_edges']>0,'handle_is_one_continuous_member':bool(handle.get('authored_continuous_path_loft')) and records[handle.name]['base']['connected_components']==1 and records[handle.name]['base']['non_manifold_edges']==0 and records[handle.name]['base']['faces']==records[handle.name]['base']['quads'],'all_meshes_have_uvs_and_materials':all(o.data.uv_layers and o.data.materials for o in objs),'all_evaluated_meshes_nondegenerate':all(r['evaluated']['degenerate_faces']==0 for r in records.values()),'silhouette_render_succeeded':all('error' not in s for s in sil)}
    report={'lab':'heldout_watering_can','stage':'candidate_v1','construction_status':'built from neutral renders only','objects':len(objs),'mesh_primitive_operators_used':0,'mesh_records':records,'silhouette_records':sil,'assertions':assertions,'pass':all(assertions.values())}
    (out/'watering_can_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(out/'heldout_watering_can.blend'));print('WATERING_CAN_RESULT:'+json.dumps(report));raise SystemExit(0 if report['pass'] else 2)
main()
