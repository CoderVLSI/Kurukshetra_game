# Rigged character models

Seven Chapter 1 characters re-exported with a skeleton, a 10x lower triangle count, and
looping `idle` and `walk` animations.
Drop each file over the same-named file in `assets/models/` of the Godot project
(Godot re-imports automatically).

| Model | Triangles before | Triangles after | Size before | Size after |
|---|---|---|---|---|
| Yudhishthira | 500,000 | 50,000 | 31.4 MB | 13.4 MB |
| Bhima | 500,000 | 50,000 | 30.8 MB | 12.1 MB |
| Sahadeva | 500,000 | 50,000 | 32.4 MB | 14.3 MB |
| Nakula | 500,000 | 50,000 | 33.0 MB | 14.4 MB |
| Dronacharya | 500,000 | 50,000 | 33.0 MB | 15.1 MB |
| Vidura | 500,000 | 50,000 | 32.6 MB | 15.2 MB |
| Duryodhana | 500,000 | 50,000 | 32.3 MB | 13.5 MB |

- Same 27-bone skeleton and bone names as Arjuna, Krishna, Bhishma and Karna
  (`pelvis`, `spine_01..03`, `upperarm_l`, `hand_r`, `thigh_l`, `foot_ik_l`, ...), so the
  existing rig scripts (`archery_rig.gd`, `charioteer_rig.gd`) can drive them.
- Position, scale and orientation are unchanged: bounding boxes match the originals within
  0.001 m, so the commander placements in `chapter.gd` still line up.
- Textures and material slots are unchanged (2048x2048 albedo, roughness/metallic, normal).
- Each file contains an `AnimationPlayer` with two clips, both set to loop on import:
  `idle` (4.0 s: breathing, slow weight shift, tiny head drift) and
  `walk` (1.2 s per full cycle, in place, no root motion).
- Play them in Godot like this:

  ```gdscript
  var ap := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
  ap.play("idle")
  ap.play("walk")
  ap.speed_scale = move_speed / 1.3   # the walk is authored for ~1.3 units/s at scale 1
  ```
- Walk numbers (measured): planted-foot ground speed averages 1.29 units/s (peak 1.69,
  so there is a little foot skate in mid-stance), swing-foot clearance 0.125 units.
- The clips are written against the shared bone names, so they play on any model with the
  same skeleton. `tools/blender/locomotion.py` holds the amplitudes if you want to tune them.
- Verified in Godot 4.5.1: imports cleanly, boots, gallery and palace scene render
  (see `docs/rigged-characters-ingame.png`), and the walk cycle was captured in the game
  engine (`docs/walk-cycle-ingame.png`: Duryodhana, Vidura, Bhima).

Not done: Dhritarashtra and Sanjaya (seated, Dhritarashtra is fused with his throne), and
the generic ArmyArcher / ArmyShield soldiers.

Project check to update: `new_models_check.gd` asserts exactly 500,000 triangles per
character and will now fail by design.

## Rebuilding

Per-character settings (leg offsets measured from each model's feet) live in
`tools/blender/characters.json`. Rebuild everything from the original 500k-triangle GLBs with
`tools/blender/build_all.sh <originals dir> <output dir> [jobs] [Name ...]` (about 6-7 minutes
for all seven on 4 cores). Single character: see the usage notes at the top of
`tools/blender/rig_character.py` (add `"animate":1` to its options to bake in the clips).
