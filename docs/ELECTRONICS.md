# Electronics, Firmware and Calibration

## Wiring overview

```
             12 V 15 A PSU ──► RAMPS 1.4 (12 V in) ──── Arduino Mega 2560 ── USB ── PC (Ravi.py)
                                   │
  X socket  TMC2209 ── J1 base     │  X-MIN  (D3)  ── J1 switch
  Y socket  (empty) ─┐             │  Y-MIN  (D14) ── J2 switch
  Z socket  TMC2209 ── J3 elbow    │  Z-MIN  (D18) ── J3 switch
  E0 socket TMC2209 ── J4 roll     │  D42 (AUX)    ── J4 switch
  E1 socket TMC2209 ── J5 wrist    │  D44 (AUX)    ── J5 switch
                     │             │  A9  (AUX-2)  ── E-stop contact 2 (grbl reset) to GND
                     │             │  D10 (12 V MOSFET out, M8) ── 12 V relay coil (diode across coil)
                     │
  Y STEP (A6) ── PUL+  ┐
  Y DIR  (A7) ── DIR+  ├─ DM542T ── J2 NEMA23            24–36 V 5 A PSU ──► DM542T
  Y EN   (A2) ── ENA+  │   PUL− / DIR− / ENA− ── RAMPS GND
                       ┘
  Relay contacts (NO) ──── E-stop contact 1 (NC) ──── welder torch-trigger pair   (Phase 2)
                                                └──── or an LED + resistor           (Phase 1)
```

Pin numbers are from the grbl-Mega-5X RAMPS map (`cpu_map.h`, `CPU_MAP_2560_RAMPS_BOARD`). grbl reads both the MIN and MAX limit pins of each axis. One normally-open switch to GND on the MIN pin is enough, with internal pull-ups and `$5=0`.

### Notes

- **Run the RAMPS at 12 V.** Its stock fuses, capacitors and the Mega's regulator path are made for 12 V. The NEMA23 has its own driver and supply.
- **DM542T:** set the DIP switches to 3200 pulses/rev (16 microsteps, matching `robot.json`). Set peak current to about the motor rating, and standstill current to **full**, because the shoulder holds the arm against gravity.
- **TMC2209 / DRV8825:** set 16 microsteps and adjust each driver's current (Vref) to about 70–80 % of the motor rating.
- **Relay on D10:** D10 switches the low side of a 12 V load. Wire the relay coil between D10's + and − terminals and put a 1N4007 diode across the coil (band towards +). A relay module with its own diode works too.
- **E-stop:** use a mushroom E-stop with two NC contacts.
  - Contact 1 sits in series with the relay contacts, so pressing it breaks the trigger circuit in hardware even if the software hangs.
  - Contact 2 pulls A9 (grbl reset) to GND. Reset stops motion at once and switches the coolant/arc output off.
  - Motors stay energised and hold the arm (it doesn't drop).
- **Grounding:** the Mega, RAMPS and DM542T share GND. In Phase 2 the welding work lead goes to the workpiece only, never to the robot or the controller.

## Firmware: grbl-Mega-5X

1. Download grbl-Mega-5X from <https://github.com/fra589/grbl-Mega-5X>.
2. In `grbl/config.h`, check or change these lines:

   ```c
   #define DEFAULTS_GENERIC
   #define CPU_MAP_2560_RAMPS_BOARD
   #define N_AXIS 5
   #define AXIS_4_NAME 'A'
   #define AXIS_5_NAME 'B'

   // Homing order for the arm: elbow, shoulder, base, then the wrist.
   // Replace the "#elif N_AXIS == 5" homing block with:
   #define HOMING_CYCLE_0 (1<<AXIS_3)                 // J3 elbow
   #define HOMING_CYCLE_1 (1<<AXIS_2)                 // J2 shoulder
   #define HOMING_CYCLE_2 (1<<AXIS_1)                 // J1 base
   #define HOMING_CYCLE_3 ((1<<AXIS_4)|(1<<AXIS_5))   // J4 + J5 wrist
   ```

3. Copy the `grbl` folder into your Arduino `libraries` folder.
4. Open `examples/grblUpload` and upload it to the Mega (board: *Arduino Mega or Mega 2560*).
5. In a serial terminal at 115200 baud, run `$RST=*` once.
6. Load the robot's settings, which are generated from `config/robot.json`:

   ```bash
   python Ravi.py grbl-settings                          # print them
   python Ravi.py grbl-settings --port /dev/ttyACM0      # or upload them directly
   ```

   These set steps per **degree**, max rates (deg/min), accelerations (deg/s²), homing direction and `$1=255`, which keeps the motors powered so the arm doesn't sag.

## Bring-up checklist

Have one hand on the E-stop for every step.

1. **No motors connected:** `?` in the terminal returns `<Idle|...>` or `<Alarm|...>`.
2. **Directions.** Unlock with `$X`, then use small relative jogs, for example `$J=G91 X5 F300` and `$J=G91 Y2 F120`. Check each joint against the + directions in [ASSEMBLY.md](ASSEMBLY.md). Fix any reversed joint with the `$3` direction-invert mask (bit 0 = J1 … bit 4 = J5).
3. **Switches:** press each switch by hand and watch `?`. The `Pn:` field shows X, Y, Z, A, B.
4. **Homing:** `python Ravi.py home --port /dev/ttyACM0`. It runs `$H`, sets each joint to its `home` angle with `G10 L20 P1`, then moves to the ready pose (all joints 0).

## Calibration

The goal is to make the software's joint angles match the real joint angles.

1. **Joint zeros.** After homing, jog each joint until it matches its zero (use a square or an angle finder on the links: J2 vertical, J3 at 90° to J2, and so on). Read the position with `?`. The offset you jogged is the error in that joint's `home` value. Fix `home` in `config/robot.json`, re-home, and repeat until it's within 0.2°.
2. **Tool length.** Move the pointer to touch a point, then rotate J5 by ±20° with a pose that keeps the tip on the same point (`python Ravi.py pose X Y Z --dir ...` with two different directions). If the tip wanders, adjust `"tool"` until it doesn't.
3. **Check against a ruler.** Command `pose` targets at the four corners of the work block and measure where the pointer lands. Log the errors. Within ±2 mm passes Phase 1 (milestone M4).
4. **Backlash.** Push the tool gently by hand in each direction at a fixed pose and measure the movement. Note it in your test log, because it limits weave accuracy.
