# Bill of Materials: Phase 1 (desktop prototype)

Prices are rough single-unit online prices in USD, to help with budgeting. A machine-readable copy is in [bom.csv](bom.csv). For the hardware each printed part needs, with pictures, see the **[Parts Catalog](PARTS.md)**.

## Motion

| Qty | Part | Used for | Notes | ~USD |
|---|---|---|---|---|
| 2 | NEMA17 48 mm stepper (1.68 A) with planetary gearbox ≈27:1 (exact 26.85:1), 8 mm D-shaft, e.g. StepperOnline **17HS19-1684S-PG27** | J1 base, J3 elbow | Max permissible output torque 3 N·m. Sellers list no-load backlash between 1° and 3°. | 70 |
| 2 | NEMA17 34 mm stepper with planetary gearbox ≈5:1 (exact 5.18:1), 8 mm D-shaft, e.g. StepperOnline **17HS13-0404S-PG5** | J4 roll, J5 wrist | The 48 mm `17HS19-1684S-PG5` also works, but is heavier. | 55 |
| 1 | NEMA23 56 mm stepper (2.8 A, ≥1.2 N·m) with 10:1 planetary gearbox, 14 mm keyed shaft, **bought as one unit** | J2 shoulder | Gearbox rated output ≥10 N·m | 80 |
| 2 | 6008-2RS bearing (40×68×15) | J1 turntable | | 10 |
| 2 (+2 spare) | 608-2RS bearing (8×22×7) | J2/J3 idle-side pivots | | 4 |

> **Measure the gearboxes before printing.** Planetary gearboxes differ between vendors: pilot diameter, bolt circle, screw size, shaft length and key. Enter your values in `cad/config.scad` (`GM17_48`, `GM17_34`, `GM23_56`), then rebuild the STLs.

## Electronics

| Qty | Part | Notes | ~USD |
|---|---|---|---|
| 1 | Arduino Mega 2560 (or clone) | runs grbl-Mega-5X | 18 |
| 1 | RAMPS 1.4 shield | 5 driver sockets, MOSFET outputs D8/D9/D10 | 8 |
| 4 | TMC2209 step/dir driver modules (or DRV8825) | X, Z, E0, E1 sockets: J1, J3, J4, J5 | 20 |
| 1 | DM542T (or similar) external stepper driver | J2 NEMA23, wired to the Y socket signals | 30 |
| 1 | 12 V 15 A power supply | RAMPS (its stock parts are rated 12 V) | 25 |
| 1 | 24–36 V 5 A power supply | DM542T only | 22 |
| 5 | Lever microswitch, KW11 / SS-5GL size (M2 holes 9.5 mm apart) | homing switches | 6 |
| 1 | 12 V relay module (or 12 V relay + 1N4007 diode) | "arc on" output from D10. Phase 1: switch an LED | 4 |
| 1 | Mushroom E-stop, 2 × NC contacts | contact 1: arc loop, contact 2: grbl reset (A9) | 10 |
| 1 | Mains inlet with switch and fuse | | 6 |
| — | 4-core shielded cable (~10 m), 2-core for switches (~8 m), ferrites, crimp connectors, spiral wrap | | 30 |

## Fasteners and hardware

| Qty | Part | Where |
|---|---|---|
| 20 | M3 brass heat-set insert (Ø4.2 hole, ~5.7 mm long) | shell bosses (6), tower (3), deck switch (2), turntable (3), spares |
| 6 | M3 × 10 countersunk | floor → shell |
| 3 | M3 × 10 button head | J1 motor mount → tower |
| 4 | M3 × 10 button head (ISO 7380) | J1 gearbox face |
| 12 | M3 × 8 button head | J3, J4, J5 gearbox faces (check your gearbox's thread depth) |
| 4 | M5 × 14 button head | J2 gearbox face |
| 3 | M3 × 50 socket head | collar → spigot → turntable (bearing preload) |
| 4 | M4 × 65 socket head + M4 nuts | upper arm halves |
| 8 | M3 × 45 socket head + M3 nuts | forearm halves |
| 1 + 1 | M8 × 50 and M8 × 45 bolt, M8 nylock nuts, washers | shoulder and elbow idle pivots |
| 5 | M3 × 8 set screw (or M3 × 8 screw) + M3 nut | hub clamps on the D-flat / key |
| 1 | M3 × 16 + nut | tool clamp |
| 10 + 10 | M2 × 10 + M2 nuts | microswitches |
| 10 | M3 × 8 | endstop clips |

## Printing and Phase 1 tool

| Qty | Part | Notes | ~USD |
|---|---|---|---|
| 1 kg + 1 kg | PETG (or ASA) filament: orange (arm, covers) + graphite/black (base, turntable, small parts) | ~0.55 kg orange + ~0.95 kg graphite used | 40 |
| 1 | White paint pen | fills the RAVI / WR-1 lettering | 4 |
| 1 | Ø12 mm pointer: aluminium rod with a sharpened tip, or a 12 mm laser dot module | for calibration (TCP) | 5 |
| 1 | Fine marker refill in a printed or taped 12 mm sleeve | pen-drawing tests | 2 |
| 1 | 100 mm tall work block (wood or steel, ~200 × 160 mm top) | sets the work height the examples assume | — |

**Phase 1 total: about $450–550**, plus a 3D printer with a 220 × 220 mm bed and basic tools: calipers, hex keys, a soldering iron for inserts and a multimeter.
