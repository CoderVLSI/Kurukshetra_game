extends SceneTree
func _init():
	for name_ in OS.get_cmdline_user_args():
		var ps := load("res://assets/models/%s.glb" % name_) as PackedScene
		var n := ps.instantiate() as Node3D
		root.add_child(n)
		var tris := 0
		var aabb := AABB()
		var first := true
		for mi in n.find_children("*","MeshInstance3D",true,false):
			var m := mi as MeshInstance3D
			for s in m.mesh.get_surface_count():
				var arr := m.mesh.surface_get_arrays(s)
				tris += arr[Mesh.ARRAY_INDEX].size()/3 if arr[Mesh.ARRAY_INDEX] != null else 0
			var a := m.global_transform * m.get_aabb()
			aabb = a if first else aabb.merge(a)
			first = false
		var sks := n.find_children("*","Skeleton3D",true,false)
		var line := "%s tris=%d aabb_min=%s aabb_max=%s skeletons=%d" % [name_, tris, aabb.position, aabb.end, sks.size()]
		if sks.size() > 0:
			var sk := sks[0] as Skeleton3D
			line += " bones=%d has[upperarm_l,hand_r,spine_02,head]=%s" % [sk.get_bone_count(), [sk.find_bone("upperarm_l")>=0, sk.find_bone("hand_r")>=0, sk.find_bone("spine_02")>=0, sk.find_bone("head")>=0]]
		print("CHECK ", line)
		n.queue_free()
	quit()
