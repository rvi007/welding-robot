#!/usr/bin/env python3
"""Ravi WR-1 welding robot: main program.

    python Ravi.py info                         robot summary
    python Ravi.py pose 230 0 80                joint angles for a torch tip position (torch pointing down)
    python Ravi.py fk 0 30 10 0 0               tip position for joint angles
    python Ravi.py torque                       are the motors strong enough?
    python Ravi.py reach --z 100                where on the work block can the torch work well?
    python Ravi.py plan jobs/fillet_straight.json --png --gif
    python Ravi.py grbl-settings [--port /dev/ttyACM0]
    python Ravi.py home --port /dev/ttyACM0
    python Ravi.py jog --port /dev/ttyACM0 0 0 0 0 0
    python Ravi.py run out/fillet_straight.gcode --port /dev/ttyACM0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from robot import config, firmware, gcode, kinematics, statics, weld

OUT = Path(__file__).resolve().parent / "out"


def _robot(args):
    return config.load(args.config)


def cmd_info(args):
    r = _robot(args)
    print(r.name)
    print(f"  shoulder height {r.d1:.0f} mm, upper arm {r.l2:.0f} mm, forearm {r.l3:.0f} mm, "
          f"tool {r.tool:.0f} mm, max reach from shoulder {r.l2 + r.l3 + r.tool:.0f} mm")
    print(f"  {'joint':<17} axis  {'range (deg)':>14}  {'steps/deg':>9}  {'max deg/s':>9}")
    for j in r.joints:
        print(f"  {j.name:<17} {j.axis:^4}  {j.min:>6.0f} .. {j.max:<5.0f}  "
              f"{j.steps_per_degree:9.2f}  {j.max_speed:9.0f}")


def cmd_pose(args):
    r = _robot(args)
    q = kinematics.ik(r, args.xyz, args.dir)
    p = kinematics.fk(r, q)
    print("joints (deg): " + "  ".join(f"{j.axis}={v:.2f}" for j, v in zip(r.joints, q)))
    print(f"check  tip {np.round(p.tip, 3).tolist()}  dir {np.round(p.direction, 4).tolist()}")


def cmd_fk(args):
    r = _robot(args)
    p = kinematics.fk(r, args.joints)
    print(f"tip (mm): {np.round(p.tip, 2).tolist()}")
    print(f"torch direction: {np.round(p.direction, 4).tolist()}")
    for k in ("shoulder", "elbow", "wrist"):
        print(f"{k:>9}: {np.round(p.points[k], 1).tolist()}")


def cmd_torque(args):
    text, ok = statics.report(_robot(args))
    print(text)
    return 0 if ok else 1


REACH_DIRS = {
    "torch straight down": [0, 0, -1],
    "45 deg, pointing away from robot": [1, 0, -1],
    "45 deg, pointing back at robot": [-1, 0, -1],
    "45 deg, pointing sideways": [0, 1, -1],
}


def cmd_reach(args):
    """Map of how comfortable the wrist is at each X (Y=0) for a few torch directions."""
    r = _robot(args)
    xs = range(100, 341, 20)
    print("# good   + ok   ! close to the wrist singularity (torch in line with forearm)   . unreachable")
    for z in args.z:
        print(f"\nwork height Z={z:.0f} mm        X: " + "".join(f"{x:>4d}" for x in xs))
        for label, d in REACH_DIRS.items():
            row = ""
            for x in xs:
                try:
                    q = kinematics.ik(r, [x, 0, z], d)
                    margin = 90 - abs(q[4])
                    row += "   #" if margin >= 30 else "   +" if margin >= 15 else "   !"
                except kinematics.Unreachable:
                    row += "   ."
            print(f"  {label:<33}" + row)
    return 0


def cmd_plan(args):
    r = _robot(args)
    job = weld.load_job(args.job)
    plan = weld.plan_job(job)
    try:
        traj = gcode.solve(plan, r)
    except gcode.PlanError as e:
        print(f"PLAN FAILED: {e}", file=sys.stderr)
        return 2
    stem = Path(args.job).stem
    out = Path(args.output) if args.output else OUT / f"{stem}.gcode"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(gcode.to_gcode(traj, r, arc_enabled=args.arc))
    moves = sum(1 for s in traj.steps if s.kind == "move")
    print(f"{plan.name}: {moves} moves, weld length {plan.weld_length():.0f} mm, "
          f"about {traj.duration(r):.0f} s")
    print(f"G-code -> {out}" + ("" if args.arc else "   (dry run: add --arc to drive the arc relay)"))
    for w in traj.warnings:
        print(f"WARNING: {w}")
    if args.png or args.gif:
        from robot import sim
        if args.png:
            png = out.with_suffix(".png")
            sim.save_png(traj, str(png))
            print(f"preview -> {png}")
        if args.gif:
            gif = out.with_suffix(".gif")
            sim.save_gif(traj, str(gif))
            print(f"animation -> {gif}")
    return 0


def cmd_grbl_settings(args):
    r = _robot(args)
    text = firmware.as_text(r)
    if not args.port:
        print(text, end="")
        return 0
    from robot.sender import Grbl
    g = Grbl(args.port)
    for key, value, _ in firmware.settings(r):
        g.command(f"{key}={value}")
        print(f"{key}={value}")
    g.close()
    return 0


def cmd_home(args):
    from robot.sender import Grbl
    r = _robot(args)
    g = Grbl(args.port)
    print("homing... (keep a hand on the E-stop)")
    g.home(r)
    g.move_joints(r, r.ready_pose)
    print(g.status())
    g.close()


def cmd_jog(args):
    from robot.sender import Grbl
    r = _robot(args)
    for j, v in zip(r.joints, args.joints):
        if not j.in_range(v):
            print(f"{j.name}: {v} is outside {j.min}..{j.max}", file=sys.stderr)
            return 2
    g = Grbl(args.port)
    g.move_joints(r, args.joints)
    print(g.status())
    g.close()
    return 0


def cmd_run(args):
    from robot.sender import Grbl
    lines = Path(args.gcode).read_text().splitlines()
    strikes_arc = any(ln.strip().startswith("M8") for ln in lines)
    if strikes_arc:
        print("This program switches the WELDING ARC on.")
        print("Helmet down, gloves on, fire extinguisher at hand, nobody near the arm.")
        if input("Type ARC to continue: ").strip() != "ARC":
            print("cancelled")
            return 1
    g = Grbl(args.port)

    def progress(i, n, line):
        print(f"\r{i}/{n}  {line[:60]:<60}", end="", flush=True)

    try:
        g.stream(lines, progress)
        print("\ndone")
    except KeyboardInterrupt:
        g.stop()
        print("\nSTOPPED (feed hold + reset, arc output off). Re-home before the next run.")
        return 1
    finally:
        g.close()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="Ravi.py", description="Ravi WR-1 welding robot toolkit")
    p.add_argument("--config", default=None, help="robot description (default config/robot.json)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="robot summary").set_defaults(fn=cmd_info)

    s = sub.add_parser("pose", help="inverse kinematics for a tip position")
    s.add_argument("xyz", type=float, nargs=3)
    s.add_argument("--dir", type=float, nargs=3, default=[0, 0, -1], help="torch direction")
    s.set_defaults(fn=cmd_pose)

    s = sub.add_parser("fk", help="forward kinematics for joint angles")
    s.add_argument("joints", type=float, nargs=5)
    s.set_defaults(fn=cmd_fk)

    sub.add_parser("torque", help="gravity torque check for every joint").set_defaults(fn=cmd_torque)

    s = sub.add_parser("reach", help="workspace map for placing parts")
    s.add_argument("--z", type=float, nargs="+", default=[60, 100, 140], help="work heights (mm)")
    s.set_defaults(fn=cmd_reach)

    s = sub.add_parser("plan", help="weld job JSON -> G-code (+ preview)")
    s.add_argument("job")
    s.add_argument("-o", "--output")
    s.add_argument("--arc", action="store_true", help="emit M8/M9 to drive the arc relay")
    s.add_argument("--png", action="store_true", help="save a preview image")
    s.add_argument("--gif", action="store_true", help="save an animation")
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("grbl-settings", help="print (or upload) firmware settings")
    s.add_argument("--port")
    s.set_defaults(fn=cmd_grbl_settings)

    s = sub.add_parser("home", help="home all joints, then go to the ready pose")
    s.add_argument("--port", required=True)
    s.set_defaults(fn=cmd_home)

    s = sub.add_parser("jog", help="move to joint angles")
    s.add_argument("--port", required=True)
    s.add_argument("joints", type=float, nargs=5)
    s.set_defaults(fn=cmd_jog)

    s = sub.add_parser("run", help="stream a G-code program to the robot")
    s.add_argument("gcode")
    s.add_argument("--port", required=True)
    s.set_defaults(fn=cmd_run)

    args = p.parse_args(argv)
    try:
        return args.fn(args) or 0
    except kinematics.Unreachable as e:
        print(f"UNREACHABLE: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
