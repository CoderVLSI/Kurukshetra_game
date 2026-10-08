extends SceneTree
func _init():
	for name_ in OS.get_cmdline_user_args():
		var n := (load("res://assets/models/%s.glb" % name_) as PackedScene).instantiate()
		root.add_child(n)
		var ap := n.find_children("*","AnimationPlayer",true,false)
		if ap.is_empty():
			print("ANIM ", name_, " NO AnimationPlayer"); continue
		var player := ap[0] as AnimationPlayer
		var sk := n.find_children("*","Skeleton3D",true,false)[0] as Skeleton3D
		for a in player.get_animation_list():
			var anim := player.get_animation(a)
			var first_last := ""
			# loop continuity: compare first and last key of the first rotation track
			for t in anim.get_track_count():
				if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D and anim.track_get_key_count(t) > 1:
					var k := anim.track_get_key_count(t)
					var q0: Quaternion = anim.track_get_key_value(t, 0)
					var q1: Quaternion = anim.track_get_key_value(t, k-1)
					first_last = "%s firstlast_angle=%.5f" % [anim.track_get_path(t), q0.angle_to(q1)]
					break
			print("ANIM ", name_, " '", a, "' len=", anim.length, " loop_mode=", anim.loop_mode, " tracks=", anim.get_track_count(), " ", first_last)
		# sample pose: play walk, advance, read hip rotation
		player.play("walk" if player.has_animation("walk") else player.get_animation_list()[0])
		var thigh := sk.find_bone("thigh_l")
		for t in [0.0, 0.3, 0.6, 0.9]:
			player.seek(t, true)
			print("   t=", t, " thigh_l pose angle(deg)=", snappedf(rad_to_deg(sk.get_bone_pose_rotation(thigh).get_euler().x), 0.1))
		n.queue_free()
	quit()
