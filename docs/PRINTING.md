# Printing Guide

All STLs are in [`../stl`](../stl), already in print orientation (flat face down, no supports needed). They fit a 220 × 220 × 250 mm bed. The upper arm halves are 218 mm long, so place them along the bed diagonal if your printer is tight.

## Before anything else: `fit_test.stl`

Print `fit_test.stl` (about 1.5 h) in the material you will use for the robot, then check each of these:

| Feature | Good fit | If it is too tight | If it is too loose |
|---|---|---|---|
| 6008 seat (big hole) | Bearing presses in with firm thumb pressure | raise `bearing_fit` by 0.05 | lower `bearing_fit` |
| 608 seat | same | same | same |
| Gearbox pilot + 4 screw holes | Your J1/J3 gearbox face sits flat; screws line up | measure the gearbox; fix `GM17_48` | fix `GM17_48` |
| D-bore (8 mm) | Gearbox shaft slides in with slight friction; flat lines up | raise `clr` | lower `clr` |
| Keyed bore (14 mm) | J2 shaft with its key slides in | raise `clr` or `key_t2` | lower `clr` |
| Insert hole | A heat-set insert goes in straight and flush | `insert_d` | `insert_d` |

Edit [`cad/config.scad`](../cad/config.scad) and regenerate:

```bash
cad/build.sh          # needs OpenSCAD 2021.01+ on PATH (or OPENSCAD=/path/to/openscad cad/build.sh)
```

## Material and settings

Use **PETG** (or ASA). PLA is fine for a quick look, but it creeps under the constant motor load and softens in a warm room. Nothing printed may go near a real arc (see [SAFETY.md](SAFETY.md)).

Defaults for everything not listed below: 0.4 mm nozzle, 0.2 mm layers, **4 walls**, 5 top/bottom layers, **40 % gyroid** infill.

| Part | Qty | Special settings | Est. filament |
|---|---|---|---|
| `fit_test` | 1 | default | 55 g |
| `base_floor` | 1 | default | 110 g |
| `base_shell` | 1 | printed upside down (deck on the bed) | 360 g |
| `j1_motor_mount` | 1 | default | 45 g |
| `j1_spigot` | 1 | **100 % infill** (it is clamped through by the preload bolts) | 55 g |
| `j1_collar` | 1 | **100 % infill** | 22 g |
| `turntable` | 1 | 5 walls, 50 % infill; drive cheek must be stiff | 200 g |
| `upper_arm_drive` / `upper_arm_idle` | 1 + 1 | 5 walls, 50 % infill | 260 g |
| `forearm_drive` / `forearm_idle` | 1 + 1 | default | 180 g |
| `wrist` | 1 | 6 walls, 60 % infill | 15 g |
| `tool_holder` | 1 | 6 walls, 60 % infill; the hub ends overhang 1–2 mm (fine without support) | 15 g |
| `spacer_m8` | 2 | default | 1 g |
| `endstop_clip` | 5 | default | 10 g |

Total is about **1.3 kg** and **70–90 hours** of printing.

## After printing

1. **Heat-set inserts.** Set the iron to 230–245 °C for PETG. Press each insert straight in until flush. Use 14 in total:
   - base shell: 6 floor bosses, 3 on the tower underside, 2 on the deck for the J1 switch
   - turntable underside: 3
2. **Ream the pivot holes** (608 seats, 8.4 mm bolt holes) with a drill held by hand if a bearing or bolt won't go in. Don't force a bearing into a seat that's too small: it cracks the layer lines.
3. **Check the D-bores** slide onto your gearbox shafts before assembly. Remove the elephant's-foot flare on bed-side bores with a deburring tool.
