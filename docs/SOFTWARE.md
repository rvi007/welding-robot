# Software: `Ravi.py`

`Ravi.py` is the main program. It plans weld paths, solves the arm's kinematics, previews jobs, writes G-code and drives the robot over USB.

```bash
pip install -r requirements.txt
python Ravi.py info                     # geometry, joint ranges, steps per degree
python Ravi.py torque                   # are the motors strong enough?
python Ravi.py reach --z 100            # where on the work block does the torch work well?
python Ravi.py pose 230 0 100           # joint angles for a tip position (torch straight down)
python Ravi.py pose 230 0 100 --dir 0 1 -1   # ... with the torch leaning sideways 45°
python Ravi.py fk 0 30 10 0 -20         # tip position for joint angles
python Ravi.py plan jobs/fillet_straight.json --png --gif   # G-code + preview in out/
python Ravi.py home --port /dev/ttyACM0
python Ravi.py jog  --port /dev/ttyACM0 0 20 0 0 0
python Ravi.py run out/fillet_straight.gcode --port /dev/ttyACM0
python -m pytest                        # 20 tests: kinematics, planner, collisions, G-code, statics
```

On Windows the port looks like `COM3`.

## Coordinates

- Origin: the centre of the base on the table. **Z up**, **X forward** (J1 = 0), Y to the robot's left.
- All positions are in mm and all angles in degrees.
- The tool tip (TCP) is the end of the pointer, pen or welding wire.
- "Torch direction" is a vector along the torch, pointing **towards the work**. For example, `0 0 -1` is straight down.

## Weld job files (`jobs/*.json`)

```json
{
  "name": "T-joint fillet, 100 mm, zigzag weave",
  "defaults": {"speed": 6, "travel_angle": 10},
  "seams": [
    {"name": "fillet", "type": "line",
     "start": [280, 0, 100], "end": [180, 0, 100],
     "plates": [[0, 0, 1], [0, -1, 0]],
     "weave": {"pattern": "zigzag", "amplitude": 1.5, "wavelength": 3}}
  ]
}
```

Each seam produces this sequence:

1. Rapid move to a point above the start.
2. Straight approach to the start.
3. **Arc on**, then a start dwell.
4. The weld path at constant travel speed.
5. Crater dwell, then **arc off**.
6. Straight retract.

After the last seam the arm returns to the ready pose.

### Seam types

| `type` | Fields |
|---|---|
| `line` | `start`, `end` |
| `polyline` | `points` (list). The torch reorients on the spot at corners. |
| `circle` | `center`, `axis`, `radius`, `start_angle`, `sweep` (deg, + = counter-clockwise about `axis`), `start_direction` (reference for angle 0, default +X) |

### Torch orientation

| Field | Meaning |
|---|---|
| `normal` | Direction the torch comes **from** (unit vector, away from the work). For circles, it can also be `"outside"`, `"inside"`, `"axis"`, `"fillet_outside"` or `"fillet_inside"`. |
| `plates` | Instead of `normal` for fillets: the two plate surface normals. The torch bisects them (45° work angle). |
| `travel_angle` | deg, + = push (torch leans towards the travel direction), − = drag |
| `work_angle_offset` | deg, extra tilt across the joint |
| `standoff` | mm the TCP is held back from the joint line along the torch |

### Motion and process

| Field | Default | Meaning |
|---|---|---|
| `speed` | 6 | travel speed along the seam, mm/s |
| `step` | 1 | path sampling, mm (automatically finer when weaving) |
| `weave` | none | `{"pattern": "zigzag" or "sine", "amplitude": mm, "wavelength": mm}` |
| `approach`, `retract` | 30 | mm, along the torch axis |
| `approach_speed` | 15 | mm/s |
| `arc_start_dwell`, `crater_dwell` | 0.3, 0.5 | s |

Put any of these in `"defaults"` to apply them to every seam.

Optional top-level fields:

| Field | Meaning |
|---|---|
| `tool_length` | overrides `robot.json` for this job |
| `safe_pose` | joint angles to finish at |
| `keep_out` | list of boxes the wrist must not enter: `{"name": "work block", "min": [x, y, z], "max": [x, y, z]}`. Add the work block, the plates and any fixtures. |
| `clearance` | extra margin around the keep-out boxes, mm (default 5) |

### Collision check

The J5 motor hangs off the side of the wrist. When the torch leans towards that side, the motor swings down towards the work. Before writing G-code, `plan` checks three parts against every `keep_out` box at every path point:

- the J5 motor
- the wrist hub
- the front of the forearm (J4 motor).

If any of them would come within `clearance`, `plan` stops and names the part. For example, with the upright plate of a fillet on the +Y side the J5 motor would hit the work block. That's why `fillet_straight.json` puts the upright plate on the −Y side, which keeps the motor about 40 mm clear. The tool itself is not checked, because it has to touch the work.

## Placing parts: what the arm likes

`python Ravi.py reach` prints a map like this one (Z = 100 mm work block):

```
                                   X:  100 120 140 160 180 200 220 240 260 280 300 320 340
  torch straight down                 !   !   +   +   +   #   #   #   #   #   #   .   .
  45 deg, pointing away from robot    .   .   .   .   .   .   .   !   !   !   !   !   !
  45 deg, pointing back at robot      #   #   #   #   #   #   #   #   .   .   .   .   .
  45 deg, pointing sideways           #   #   #   #   #   #   #   #   #   #   #   .   .
```

`#` is good, `+` is OK, `!` means close to the wrist singularity (torch in line with the forearm), `.` is out of reach. In practice:

- **Run seams towards or away from the robot (along X), with the upright plate to one side.** Fillets then use the "sideways" row, which is good almost everywhere.
- **Weld towards the robot with a push angle.** The torch then leans back towards the base, which keeps the wrist comfortable.
- **Avoid making the torch point away from the robot**, for example a fillet whose upright plate is on the far side. Turn the part instead.
- **For tubes**, the arm covers the far side and both flanks (about 240°). Turn the part for the rest, or add a positioner (Phase 2).

The planner never silently flips the wrist. If a path would make a joint jump more than 15° between two 1 mm steps, `plan` stops and tells you where.

## How it works

| Module | Job |
|---|---|
| `robot/config.py` | Loads `config/robot.json` (geometry, joints, motors, masses) |
| `robot/kinematics.py` | Closed-form FK/IK. J1–J3 place the wrist centre, J4–J5 aim the torch. Picks the wrist solution closest to the previous pose. |
| `robot/weld.py` | Seams → approach/arc/weld/crater/retract operations, torch angles, weave |
| `robot/collision.py` | Keeps the J5 motor, wrist hub and forearm front out of the job's `keep_out` boxes |
| `robot/gcode.py` | Solves the IK for every sample, checks joint limits, jumps, collisions and joint speeds, then writes `G93` inverse-time G-code. `M8`/`M9` are only written with `--arc`. |
| `robot/statics.py` | Gravity torque on each joint over the whole joint range |
| `robot/firmware.py` | grbl `$` settings from `robot.json` |
| `robot/sender.py` | USB streaming, homing (`$H` + `G10 L20`), stop (feed hold + reset) |
| `robot/sim.py` | Matplotlib preview images and GIFs |

Why `G93`: in inverse-time mode, each line says "finish this move in *t* seconds". The planner computes *t* from the seam distance and the travel speed. That keeps the torch speed constant no matter how the joints share the motion, and travel speed is the most important weld variable after current. If a joint can't keep up, the move is stretched and `plan` prints a warning.
