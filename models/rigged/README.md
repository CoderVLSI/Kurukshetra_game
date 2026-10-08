# Rigged character models

Seven Chapter 1 characters re-exported with a skeleton and a 10x lower triangle count.
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
- No animations are included. These are rigged, not yet animated.
- Verified in Godot 4.5.1: imports cleanly, boots, gallery and palace scene render
  (see `docs/rigged-characters-ingame.png`).

Not done: Dhritarashtra and Sanjaya (seated, Dhritarashtra is fused with his throne), and
the generic ArmyArcher / ArmyShield soldiers.

Project check to update: `new_models_check.gd` asserts exactly 500,000 triangles per
character and will now fail by design.

## Per-character leg settings used

Leg x-offsets (metres, native frame) were measured from the feet in each bone-fit overlay:

| Model | thigh | calf | foot/ball |
|---|---|---|---|
| Yudhishthira | 0.116 | 0.168 | 0.21 |
| Bhima | 0.149 | 0.216 | 0.27 |
| Sahadeva | 0.116 | 0.168 | 0.21 |
| Nakula | 0.110 | 0.160 | 0.20 |
| Dronacharya | 0.121 | 0.176 | 0.22 |
| Vidura | 0.094 | 0.136 | 0.17 |
| Duryodhana | 0.150 | 0.230 | 0.285 |

Rebuild one: see `tools/blender/rig_character.py`. Decimate ratio was 0.1 for all.
