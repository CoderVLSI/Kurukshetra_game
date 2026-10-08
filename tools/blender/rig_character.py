"""Decimate, rig and export a character GLB for Kurukshetra.

Usage (Blender 4.0+, needs python3-numpy for the glTF importer):
  blender -b --factory-startup --python rig_character.py -- \
      <src.glb> <Name> <out.glb> <render_dir> <decimate_ratio> ['<json options>']

Steps: weld vertices -> collapse-decimate -> fit the 27-bone template skeleton
(template.json, taken from Arjuna.glb) -> automatic weights -> posed render test
-> GLB export in the model's native frame. Options (JSON): x = per-joint absolute
x offsets {"thigh","calf","foot","ball"}, z / y likewise, sx = x scale override,
overlay_only = only render the bone-fit overlay and stop.
"""
import bpy,sys,os,json,math,bmesh,mathutils
a=sys.argv[sys.argv.index('--')+1:]
S=os.path.dirname(os.path.abspath(__file__))
src,name,out_glb,rdir=a[:4]; ratio=float(a[4]); opts=json.loads(a[5]) if len(a)>5 else {}
sys.path.insert(0,S); import render_lib as rlib
T=json.load(open(S+'/template.json'))['bones']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src, merge_vertices=True)
o=[x for x in bpy.data.objects if x.type=='MESH'][0]
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
o.name='SK_%s_LOD0'%name
# weld + decimate
bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5); bm.to_mesh(o.data); bm.free()
bpy.context.view_layer.objects.active=o; o.select_set(True)
m=o.modifiers.new('dec','DECIMATE'); m.decimate_type='COLLAPSE'; m.ratio=ratio; m.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier='dec'); bpy.ops.object.shade_smooth()
print("MESH tris",len(o.data.polygons))
# measurements in native frame
vs=[o.matrix_world@v.co for v in o.data.vertices]
zmin=min(v.z for v in vs); zmax=max(v.z for v in vs); H=zmax-zmin
xr=max(abs(v.x) for v in vs); yc=(min(v.y for v in vs)+max(v.y for v in vs))/2
Sz=H/1.85; Sx=opts.get('sx', xr/0.42); Sy=Sz
print("FIT H",round(H,3),"xr",round(xr,3),"Sz",round(Sz,3),"Sx",round(Sx,3),"zmin",round(zmin,3))
def mp(p): return mathutils.Vector((p[0]*Sx, yc+p[1]*Sy, zmin+p[2]*Sz))
arm_d=bpy.data.armatures.new(name+'_Rig'); arm=bpy.data.objects.new(name+'_Rig',arm_d); bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='EDIT')
eb={}
for b in T:
    e=arm_d.edit_bones.new(b['name']); e.head=mp(b['head']); e.tail=mp(b['tail']); e.roll=b['roll']; eb[b['name']]=e
for b in T:
    if b['parent']: eb[b['name']].parent=eb[b['parent']]
# per-character joint overrides (native frame, absolute): {"x": {"thigh":0.15}, "z": {...}} applied to both sides (x mirrored)
for k,v in opts.get('x',{}).items():
    for sd,sg in (('_l',1),('_r',-1)):
        h=eb[k+sd].head; eb[k+sd].head=mathutils.Vector((v*sg,h.y,h.z))
for k,v in opts.get('z',{}).items():
    for sd in ('_l','_r'):
        h=eb[k+sd].head; eb[k+sd].head=mathutils.Vector((h.x,h.y,zmin+v*H))
for k,v in opts.get('y',{}).items():
    for sd in ('_l','_r'):
        h=eb[k+sd].head; eb[k+sd].head=mathutils.Vector((h.x,yc+v,h.z))
# chain bones: tail follows child head (template tails equal child heads)
tt={b['name']:b for b in T}
for b in T:
    for c in T:
        if c['parent']==b['name'] and all(abs(c['head'][i]-b['tail'][i])<1e-4 for i in range(3)) and not c['name'].endswith(('_ik_l','_ik_r')):
            eb[b['name']].tail=eb[c['name']].head
# IK helpers sit at hands/feet
for sd in ('_l','_r'):
    for ik,src_ in (('hand_ik','hand'),('foot_ik','foot')):
        h=eb[src_+sd].head.copy(); eb[ik+sd].head=h; eb[ik+sd].tail=h+mathutils.Vector((0,-0.2*Sy,0))
bpy.ops.object.mode_set(mode='OBJECT')
# overlay render
def overlay(path,az=0):
    sc=bpy.context.scene
    for mat in o.data.materials:
        p=mat.node_tree.nodes.get('Principled BSDF'); 
        if p: p.inputs['Alpha'].default_value=0.28
    objs=[]
    for b in arm_d.bones:
        h=arm.matrix_world@b.head_local; t=arm.matrix_world@b.tail_local
        cd=bpy.data.curves.new('c','CURVE'); cd.dimensions='3D'; sp=cd.splines.new('POLY'); sp.points.add(1)
        sp.points[0].co=(*h,1); sp.points[1].co=(*t,1); cd.bevel_depth=0.012
        co=bpy.data.objects.new('b',cd); bpy.context.collection.objects.link(co)
        mt=bpy.data.materials.new('r'); mt.use_nodes=True
        nt=mt.node_tree; nt.nodes.clear(); em=nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value=(1,0.1,0.1,1) if not b.name.endswith('_ik_l') else (1,.5,0,1); em.inputs[1].default_value=6
        out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0],out.inputs[0]); co.data.materials.append(mt); objs.append(co)
    rlib.setup_render(520,780,16); rlib.shot(path,(0,0,(zmin+zmax)/2),6,az,ortho_scale=H*1.12)
    for co in objs: bpy.data.objects.remove(co)
    for mat in o.data.materials:
        p=mat.node_tree.nodes.get('Principled BSDF')
        if p: p.inputs['Alpha'].default_value=1.0
overlay(rdir+'/%s_bones.png'%name)
if opts.get('overlay_only'): sys.exit(0)
# skin
for n in ['root','hand_ik_l','hand_ik_r','foot_ik_l','foot_ik_r']: arm_d.bones[n].use_deform=False
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
unw=sum(1 for v in o.data.vertices if sum(g.weight for g in v.groups)<0.01)
print("SKIN vgroups",len(o.vertex_groups),"unweighted verts",unw,"of",len(o.data.vertices))
if unw:
    from mathutils.kdtree import KDTree
    ok=[v for v in o.data.vertices if sum(g.weight for g in v.groups)>=0.01]
    kd=KDTree(len(ok))
    for i,v in enumerate(ok): kd.insert(v.co,i)
    kd.balance()
    for v in o.data.vertices:
        if sum(g.weight for g in v.groups)<0.01:
            _,i,_=kd.find(v.co)
            for g in ok[i].groups: o.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
    print("SKIN fixed; unweighted now",sum(1 for v in o.data.vertices if sum(g.weight for g in v.groups)<0.01))
# pose test
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='POSE')
def rot(bn,axis,deg):
    pb=arm.pose.bones[bn]; pb.rotation_mode='XYZ'; pb.rotation_euler[axis]=math.radians(deg)
rot('upperarm_l',1,-45); rot('upperarm_r',1,45); rot('lowerarm_l',1,-50); rot('thigh_l',0,-40); rot('thigh_r',0,25); rot('spine_02',0,12); rot('head',2,25)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.context.view_layer.update()
rlib.setup_render(520,780,16); rlib.shot(rdir+'/%s_pose.png'%name,(0,0,(zmin+zmax)/2),6,0,ortho_scale=H*1.12)
rlib.shot(rdir+'/%s_pose_side.png'%name,(0,0,(zmin+zmax)/2),6,60,ortho_scale=H*1.12)
# reset pose and export
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT'); bpy.ops.pose.transforms_clear(); bpy.ops.object.mode_set(mode='OBJECT')
for x in list(bpy.data.objects):
    if x.type not in ('MESH','ARMATURE'): bpy.data.objects.remove(x)
bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB', export_apply=False, export_skins=True, export_animations=False, export_yup=True)
print("EXPORTED",out_glb)
