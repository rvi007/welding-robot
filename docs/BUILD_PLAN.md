# Build Plan: Ravi WR-1 Welding Robot

This plan takes the project from nothing to a robot that welds real seams. It runs in three phases. Each phase ends with a test you can measure, so you always know when it is safe to move on.

| Phase | What you build | What it proves | Rough cost | Time (part-time) |
|---|---|---|---|---|
| **1. Desktop prototype** (this repo, Rev A) | 3D-printed 5-axis arm with geared steppers. It holds a pen or pointer instead of a torch. | Mechanics, kinematics, path planning, homing and calibration | ~$450–550 | 5–6 weeks |
| **2. Welding prototype** | Stiffer arm (aluminium links, NEMA23 motors, low-backlash gearboxes), a real MIG torch and a welding cell | That it can lay a sound bead on 3–6 mm mild steel coupons | ~$1,500–2,500 plus welder | 2–3 months |
| **3. Production cell** | Rotary positioner, seam finding, fixtures, guarding, *or* a commercial welding cobot | Repeatable welding of real parts | depends on route | — |

> Be honest about Phase 1: a printed arm with hobby motors **cannot carry a real MIG torch and its cable**. The torch, cable drag, heat, spatter and electrical noise of a real arc are too much for it. Phase 1 is where you get the motion right, cheaply, with nothing that can burn. All of the software carries over unchanged to Phase 2.

---

## 1. Requirements

| | Phase 1 target | Phase 2 target |
|---|---|---|
| Process | none (pen / pointer), arc output drives an LED | MIG/MAG (GMAW), short-circuit transfer, 0.8–0.9 mm wire |
| Payload at the tool | 0.15 kg | 1.5 kg torch + cable drag |
| Reach (shoulder to tool tip) | 410 mm | 600–800 mm |
| Repeatability | ±1 mm | ±0.3 mm |
| Path accuracy on a 100 mm seam | ±2 mm | ±0.5 mm |
| Travel speed | 2–20 mm/s | 4–12 mm/s, held within ±5 % |
| Torch angles | work angle and push/drag (travel) angle programmable | same, plus weave |
| Safety | hardware E-stop, arc output off by default | E-stop cuts the arc in hardware, welding screen, fume extraction |

## 2. Key design decisions (and why)

1. **5 axes, not 6.** A round welding torch does not need to spin about its own axis, so the robot is a standard industrial 6-axis layout without the last joint (J6). J4 and J5 meet at one point, the wrist centre. That gives a closed-form inverse kinematics solution, which is fast, exact and easy to debug. J6 can be added later for a bent-neck torch.
2. **Geared stepper motors, bought rather than printed.** Planetary NEMA17 and NEMA23 gearmotors work the first time. Printed cycloidal or belt reducers are a good later upgrade, but they add a lot of iteration. The printed parts are structural only.
3. **grbl-Mega-5X firmware on an Arduino Mega + RAMPS 1.4.** This is proven open-source firmware with motion planning, acceleration, homing and coolant outputs, on hardware many 3D-printer owners already have. Each joint is one G-code axis, in degrees.
4. **The kinematics run on the PC (`Ravi.py`), not the microcontroller.** The PC samples weld paths every 1 mm, solves the inverse kinematics and streams joint-space moves in inverse-time feed mode (`G93`). That keeps the torch at the programmed travel speed even though each joint turns at a different rate.
5. **Arc output = grbl coolant output (`M8`/`M9`, RAMPS D10).** grbl waits for all queued motion to finish before switching coolant, so the arc starts exactly at the seam start. The output drives a relay that closes the welder's torch-trigger circuit.
6. **One source of truth per domain.** `config/robot.json` holds the geometry, joint limits and motors for the software. `cad/config.scad` holds the same lengths for the CAD. Firmware settings are generated from `robot.json` (`python Ravi.py grbl-settings`).

## 3. System architecture

```
 job.json ──► Ravi.py ─────────────────────────────► G-code ─USB─► Arduino Mega + RAMPS 1.4 (grbl-Mega-5X)
 (seams,      weld planner (approach, weave, dwell)                    │ X  J1 base   TMC2209 → NEMA17 + 27:1
  angles,     inverse kinematics + singularity check                   │ Y  J2 shoulder ─► DM542T → NEMA23 + 10:1
  speeds)     joint speed limits, G93 timing                           │ Z  J3 elbow  TMC2209 → NEMA17 + 27:1
              preview PNG/GIF, torque check                            │ A  J4 roll   TMC2209 → NEMA17 + 5:1
                                                                       │ B  J5 wrist  TMC2209 → NEMA17 + 5:1
                                                                       │ limit switches → MIN pins (homing)
                                                                       │ D10 (M8) → 12 V relay ─► welder torch trigger
                                                                       └ E-stop: NC contact in the trigger loop + grbl reset
```

## 4. Phase 1: desktop prototype

### Milestones

| # | Milestone | Done when |
|---|---|---|
| M0 | Parts ordered, printer tuned | `fit_test.stl` printed: bearings press in by hand, the gearbox pilot and screws fit, shafts slide into the D-bore and keyway, an insert sets straight |
| M1 | All parts printed | 17 STLs (22 pieces) printed in PETG (see [PRINTING.md](PRINTING.md) and [PARTS.md](PARTS.md)), inserts set |
| M2 | Mechanics assembled | Every joint turns by hand through its full range with no rubbing; the arm holds the ready pose with motors off (or sags slowly, with no bind) |
| M3 | Electronics + firmware | Each joint jogs in the right direction; homing works 10 times in a row |
| M4 | Calibration | Joint zero offsets and tool length measured; FK matches a ruler to ±2 mm across the work block |
| M5 | Path test | `pen_square.json` draws a 100 mm square: sides 100 ± 2 mm, 10 repeats inside a 1 mm band |
| M6 | Weld rehearsal | `fillet_straight.json`, `butt_weave.json` and `pipe_fillet.json` run dry with a pointer that follows a real coupon's joint line; the arc LED switches on and off at the right places |

### Schedule (evenings and weekends)

| Week | Work |
|---|---|
| 1 | Order parts (gearmotors take 1–3 weeks). Print and tune `fit_test`. Measure the real gearboxes and update `cad/config.scad`, then `cad/build.sh`. |
| 2–3 | Print all parts (110–140 h of printing, ~1.5 kg PETG). Set the heat-set inserts. |
| 3–4 | Mechanical assembly ([ASSEMBLY.md](ASSEMBLY.md)). |
| 4–5 | Wiring, flash firmware, settings, limit switches, homing ([ELECTRONICS.md](ELECTRONICS.md)). |
| 5–6 | Calibration, pen tests, accuracy log. Fix whatever the tests reveal (expect a Rev B of 2–4 parts). |

### Phase 1 risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Gearbox dimensions differ from the defaults | high | Measure first, edit `GM17_*`/`GM23_*` in `cad/config.scad`, print `fit_test` before anything else |
| Gearbox backlash (sellers list 1–3° for budget planetary boxes) shows up as several mm of error at the tool | high | Gravity preloads J2/J3. Approach every seam from the same direction (the planner already does). Buy ≤20 arcmin gearboxes for Phase 2 |
| Shoulder too weak for a heavier tool | medium | `python Ravi.py torque` after weighing the real parts; add a gas spring or counterweight on J2 |
| Wrist singularity (torch in line with the forearm) | medium | `python Ravi.py reach` to place parts; the planner refuses paths that would flip the wrist |
| The J5 motor hitting the work when the torch leans towards its side | medium | Add `keep_out` boxes to every job; `plan` refuses colliding paths. Lean the torch away from the J5 motor (see SOFTWARE.md). |
| Cable snagging on J1/J4 | medium | Service loops, spiral wrap, ±150° / ±170° soft limits |
| PLA creep under constant load | medium | Print in PETG or ASA; keep the motors energised (`$1=255`) |

## 5. Phase 2: real welding

Do these in order. Do not strike an arc with the Phase 1 arm.

1. **Scale the arm.**
   - Reach: L2 = L3 = 300 mm.
   - Links: aluminium 40×40 tube or 10 mm plate.
   - J1 and J2: NEMA23 with 20:1 low-backlash (≤15 arcmin) planetary gearboxes. J3: NEMA23 10:1.
   - J4 and J5: NEMA17 with 10:1 precision planetary gearboxes.
   - Update `config/robot.json` and rerun `Ravi.py torque` with a 1.5 kg tool and cable drag.
2. **Torch.**
   - Use a straight-neck (0°) MIG torch head, or a machine/robot MIG torch.
   - Clamp it in an insulated holder (G10/phenolic) so the robot is never in the welding circuit.
   - Fit a spring-loaded breakaway mount with a switch wired to feed hold.
   - Support the cable from above with a balancer or boom so the arm doesn't carry it.
3. **Welder interface.**
   - Use a MIG welder in 2T mode. The relay contacts close the torch-trigger pair (on a Euro torch connector, usually the two small control pins: check your manual).
   - Wire speed and voltage are set on the welder.
   - Put the E-stop's NC contact in series with the relay contact.
4. **Electrical noise.**
   - Clamp the work lead to the workpiece or table, never to the robot.
   - Use shielded motor and switch cables, with ferrites at the controller.
   - Bring all grounds to one point.
   - Don't use HF-start TIG near this electronics. MIG, or lift-arc TIG only.
5. **Heat and spatter.**
   - Keep printed parts at least 150 mm from the arc.
   - Fit an aluminium heat shield on the wrist and fire-resistant sleeving on cables near the torch.
6. **Welding cell.** You need:
   - a steel welding table
   - welding curtains around the robot
   - fume extraction at the torch
   - a fire extinguisher within reach
   - the operator outside the curtain, holding the E-stop.
7. **Process development.**
   - Weld coupons. Start with flat bead-on-plate, then butt joints, then fillets.
   - Use [weld procedure settings](#weld-settings-starting-point) from the welder chart.
   - Cut and etch samples to check penetration.
   - Log every run: job file, wire, gas, voltage, wire speed and result.
8. **Positioner.** Add a rotary table as a 6th axis. grbl-Mega-5X supports `N_AXIS 6`, with the C axis on RAMPS AUX-3. Pipe welds can then run all the way round.

### Weld settings starting point

These are typical short-circuit MIG settings for mild steel with 0.8 mm ER70S-6 wire and C25 or C2 gas. Always start from your welder's chart.

| Plate | Voltage | Wire speed | Travel speed | Gas |
|---|---|---|---|---|
| 2 mm | 16–17 V | 3–4 m/min | 6–8 mm/s | 10–12 l/min |
| 3 mm | 17–18 V | 4–5 m/min | 5–7 mm/s | 12–14 l/min |
| 5 mm | 18–20 V | 5–7 m/min | 4–6 mm/s | 14–16 l/min |

Set travel speed with `"speed"` in the job file. Typical torch angles are 45° work angle on fillets (the planner uses the plate bisector) and 10–15° push.

## 6. Phase 3: production

Pick one route:

- **Upgrade this design.** Add touch sensing (the wire touches the plate and a voltage sense finds the joint), a laser-line seam tracker, quick-change fixtures and a guarded cell with interlocks.
- **Buy a welding cobot,** or a used industrial welding robot with its welding package. Keep this repo for offline path planning, training and fixture design. For paid production work, this is usually the faster and safer route.

## 7. What is in this repository

| Area | Status |
|---|---|
| Kinematics, weld planner, collision check, G-code, simulator, torque check | Working and tested (`python -m pytest`, 20 tests) |
| CAD (OpenSCAD, 17 printable parts, RAVI branding, motor covers) | Rev B: generated and checked for closed meshes and bed fit, **not yet test-printed** |
| Realistic motor, gearbox, bearing and bolt models; 3D viewer; renders | Done (`cad/vitamins.scad`, `docs/viewer`) |
| Firmware | Uses grbl-Mega-5X; settings generated from `robot.json` |
| Phase 2 mechanics | Planned only (this document) |
