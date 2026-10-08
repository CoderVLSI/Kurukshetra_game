"""Procedural idle and walk cycles for the shared 27-bone Kurukshetra humanoid.

Poses are described as rotations about *armature-space* axes (x = character's left,
-y = forward, z = up) and converted to each bone's local rest frame, so the same numbers
work on every character that uses the template skeleton. Clips are keyed at 30 fps with
the last key equal to the first, so they loop seamlessly.

  idle: 4.0 s breathing, slow weight shift, tiny head drift
  walk: 1.2 s per full cycle (two steps), in place (no root motion)
"""
import bpy, math, mathutils

FPS = 30
LOOP_SUFFIX = "-loop"  # Godot turns on looping for clip names ending in -loop
CLIPS = {"idle": 120, "walk": 36}  # frames per loop


def _frame_rot(arm, bone, deg_xyz):
    """Local-space quaternion for a rotation given about armature X, Y, Z (degrees)."""
    r = arm.data.bones[bone].matrix_local.to_3x3()
    e = mathutils.Euler([math.radians(d) for d in deg_xyz], 'ZYX')  # Z applied first
    m = r.inverted() @ e.to_matrix() @ r
    return m.to_quaternion()


def _local_loc(arm, bone, vec):
    r = arm.data.bones[bone].matrix_local.to_3x3()
    return r.inverted() @ mathutils.Vector(vec)


def idle_pose(t, H):
    """t in [0,1). Returns ({bone: (rx,ry,rz) deg}, {bone: (dx,dy,dz) m})."""
    th = 2 * math.pi * t
    s, s2 = math.sin(th), math.sin(2 * th)
    rot = {
        "spine_01": (-0.6 * s, 0, 0.6 * math.sin(th + 0.8)),
        "spine_02": (-1.0 * s, 0, 0),
        "spine_03": (-0.8 * s, 0, 0),
        "neck_01": (0.5 * s, 0, 0),
        "head": (0.8 * math.sin(th - 0.6), 0, 1.6 * math.sin(th + 1.0)),
        "clavicle_l": (0, -1.2 * s, 0),
        "clavicle_r": (0, 1.2 * s, 0),
        "upperarm_l": (1.2 * math.sin(th + 0.5), 0, 0),
        "upperarm_r": (1.2 * math.sin(th + 0.5), 0, 0),
        "lowerarm_l": (-(5 + 1.5 * s), 0, 0),
        "lowerarm_r": (-(5 + 1.5 * s), 0, 0),
    }
    loc = {"pelvis": (0.003 * H * math.sin(th + 0.5), 0, 0.0015 * H * s2)}
    return rot, loc


def walk_pose(t, H):
    th = 2 * math.pi * t
    rot, loc = {}, {}
    for side, ph in (("l", th), ("r", th + math.pi)):
        hip = 21.6 * (math.sin(ph) - math.sin(3 * ph) / 9)         # + = leg forward; flatter than a sine so stance speed is even
        knee = 6 + 32 * max(0.0, math.cos(ph + 0.25)) ** 2       # flexion, foot goes back
        foot = 3 - 11 * math.sin(ph)                             # + = toes down
        rot["thigh_" + side] = (-hip, 0, 0)
        rot["calf_" + side] = (knee, 0, 0)
        rot["foot_" + side] = (foot, 0, 0)
    # arms swing against the same-side leg: left arm forward when left leg is back
    rot["upperarm_l"] = (14 * math.sin(th), 0, 0)
    rot["upperarm_r"] = (-14 * math.sin(th), 0, 0)
    rot["lowerarm_l"] = (-(10 + 10 * max(0.0, -math.sin(th))), 0, 0)
    rot["lowerarm_r"] = (-(10 + 10 * max(0.0, math.sin(th))), 0, 0)
    rot["pelvis"] = (0, 0, -5 * math.sin(th))
    rot["spine_01"] = (1.5, 0, 2.5 * math.sin(th))
    rot["spine_02"] = (1.0, 0, 2.5 * math.sin(th))
    rot["spine_03"] = (0.5, 0, 2.5 * math.sin(th))
    rot["head"] = (-2.0, 0, -2.5 * math.sin(th))
    loc["pelvis"] = (-0.012 * H * math.cos(th), 0, 0.011 * H * math.cos(2 * th))
    return rot, loc


POSES = {"idle": idle_pose, "walk": walk_pose}


def build(arm, H):
    """Create looping actions 'idle' and 'walk' on `arm`. H = character height (m)."""
    bpy.context.scene.render.fps = FPS  # exporter uses scene fps for clip length
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    arm.animation_data_create()
    for name, frames in CLIPS.items():
        act = bpy.data.actions.new(name + LOOP_SUFFIX)
        act.use_fake_user = True
        arm.animation_data.action = act
        for f in range(frames + 1):
            rot, loc = POSES[name]((f % frames) / frames, H)
            for pb in arm.pose.bones:
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = (1, 0, 0, 0)
                pb.location = (0, 0, 0)
            for b, d in rot.items():
                arm.pose.bones[b].rotation_quaternion = _frame_rot(arm, b, d)
            for b, v in loc.items():
                arm.pose.bones[b].location = _local_loc(arm, b, v)
            for b in set(rot) | set(loc):
                pb = arm.pose.bones[b]
                if b in rot: pb.keyframe_insert('rotation_quaternion', frame=f)
                if b in loc: pb.keyframe_insert('location', frame=f)
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.animation_data.action = bpy.data.actions['walk' + LOOP_SUFFIX]


def foot_report(arm, frames=CLIPS["walk"]):
    """(average, peak) stance speed in m/s that keeps the planted foot from sliding, and swing clearance in m."""
    arm.animation_data.action = bpy.data.actions['walk' + LOOP_SUFFIX]
    ys, zs = [], []
    for f in range(frames + 1):
        bpy.context.scene.frame_set(f % frames)
        p = arm.matrix_world @ arm.pose.bones['foot_l'].head
        ys.append(p.y); zs.append(p.z)
    zmin = min(zs)
    steps = [(ys[i + 1] - ys[i], zs[i]) for i in range(frames)]
    stance = [dy * FPS for dy, z in steps if dy > 0 and z < zmin + 0.06]  # foot moving back relative to body, near ground
    return (sum(stance) / len(stance), max(stance), max(zs) - zmin) if stance else (float('nan'),) * 3
