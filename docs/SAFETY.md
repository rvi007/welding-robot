# Safety

A welding robot combines two serious hazards: **a machine that moves on its own** and **an electric arc**. The arc brings UV radiation, fumes, heat, fire and high current. Read this before powering anything.

## Phase 1 (no welding)

- The arm can pinch fingers between links and hit hard enough to bruise. Stay out of its reach while it's powered, and keep a hand on the E-stop during every new program.
- `Ravi.py plan` writes **dry-run G-code by default**: the arc output (`M8`) is left out unless you pass `--arc`. `Ravi.py run` asks you to type `ARC` before it streams any program that switches the arc output on.
- In Phase 1 the arc output drives only an LED. **Do not connect a welder to the Phase 1 arm.** Its printed plastic parts and small motors are not built for a torch: plastic burns, and spatter and EMI cause dangerous misbehaviour.
- Clamp the base to the bench. At full reach the arm can tip an unclamped base.
- Mains wiring (PSU inputs) must be enclosed, fused and earthed. If you aren't qualified, have it done by someone who is.

## Phase 2 (real welding)

**Arc and fumes**
- Wear an auto-darkening helmet, leather gloves and FR clothing. Anyone watching wears the same eye protection.
- Put welding curtains around the robot so nobody gets arc flash.
- Use fume extraction at the torch, or at least strong ventilation. Never weld galvanised or coated steel without the right extraction.

**Fire**
- No flammables within 10 m.
- Keep an ABC extinguisher within reach and a welding blanket over the bench.
- Keep a fire watch for 30 minutes after the last weld.

**Electrical**
- Clamp the work lead to the workpiece or the steel table, **never** to the robot, the controller or the PC.
- Mount the torch insulated from the robot.
- Use shielded motor and switch cables.
- Don't use HF-start TIG near this electronics.

**Stopping**
- Contact 1 of the E-stop must break the welder's trigger circuit **in hardware** (in series with the relay).
- Contact 2 resets grbl, which stops motion and drops the arc output.
- Test both before every session.

**Collisions**
- Fit a breakaway torch mount with a switch wired to feed hold.
- Dry-run every new program with the arc off (no `--arc`) and the wire cut back.

**Arc start**
- Only an operator standing outside the curtain, holding the E-stop, starts a program that strikes an arc.
