import bpy, math, mathutils
def setup_render(w=480,h=720,samples=12):
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=samples; sc.cycles.device='CPU'; sc.cycles.use_denoising=False
    sc.render.resolution_x=w; sc.render.resolution_y=h; sc.render.film_transparent=False
    wd=bpy.data.worlds.new('w'); wd.use_nodes=True; wd.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.58,0.62,1); wd.node_tree.nodes['Background'].inputs[1].default_value=1.0
    sc.world=wd
    ld=bpy.data.lights.new('sun','SUN'); ld.energy=3.0; lo=bpy.data.objects.new('sun',ld); bpy.context.collection.objects.link(lo); lo.rotation_euler=(math.radians(50),0,math.radians(-30))
def shot(path,center,dist,az_deg,height=None,ortho_scale=None):
    sc=bpy.context.scene
    cd=bpy.data.cameras.new('cam'); cd.type='ORTHO'; cd.ortho_scale=ortho_scale or 2.4
    co=bpy.data.objects.new('cam',cd); bpy.context.collection.objects.link(co); sc.camera=co
    a=math.radians(az_deg); co.location=(center[0]+dist*math.sin(a)*-1*-1, center[1]-dist*math.cos(a), center[2])
    co.location=(center[0]+dist*math.sin(a), center[1]-dist*math.cos(a), center[2])
    d=mathutils.Vector(center)-co.location; co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(co)
