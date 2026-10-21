"""grbl-Mega-5X '$' settings derived from config/robot.json."""

from __future__ import annotations

from .config import Robot


def homing_dir_mask(robot: Robot) -> int:
    """Bit set = search in the negative direction (switch sits at the joint's minimum)."""
    mask = 0
    for i, j in enumerate(robot.joints):
        if abs(j.home - j.min) < abs(j.home - j.max):
            mask |= 1 << i
    return mask


def settings(robot: Robot) -> list[tuple[str, str, str]]:
    rows = [
        ("$0", "10", "step pulse, microseconds"),
        ("$1", "255", "keep motors energised when idle (the arm must hold against gravity)"),
        ("$2", "0", "step pulse invert mask"),
        ("$3", "0", "direction invert mask: set bits for joints that turn the wrong way"),
        ("$4", "0", "step enable invert"),
        ("$5", "0", "limit pins invert (0 = normally-open switches to GND)"),
        ("$10", "1", "status report: machine position"),
        ("$11", "0.010", "junction deviation"),
        ("$13", "0", "report in mm (here: degrees)"),
        ("$20", "0", "soft limits off: Ravi.py checks joint limits before writing G-code"),
        ("$21", "0", "hard limits off until every switch is tested"),
        ("$22", "1", "homing cycle enabled"),
        ("$23", str(homing_dir_mask(robot)), "homing direction mask (computed from 'home' angles)"),
        ("$24", "60", "homing locate rate, deg/min"),
        ("$25", "600", "homing seek rate, deg/min"),
        ("$26", "250", "homing debounce, ms"),
        ("$27", "2.000", "homing pull-off, deg"),
    ]
    for i, j in enumerate(robot.joints):
        rows.append((f"$10{i}", f"{j.steps_per_degree:.3f}", f"{j.name}: steps per degree"))
    for i, j in enumerate(robot.joints):
        rows.append((f"$11{i}", f"{j.max_speed * 60:.0f}", f"{j.name}: max rate, deg/min"))
    for i, j in enumerate(robot.joints):
        rows.append((f"$12{i}", f"{j.accel:.0f}", f"{j.name}: acceleration, deg/s^2"))
    for i, j in enumerate(robot.joints):
        rows.append((f"$13{i}", f"{j.max - j.min:.0f}", f"{j.name}: max travel, deg"))
    return rows


def as_text(robot: Robot) -> str:
    out = [f"; grbl-Mega-5X settings for {robot.name}",
           "; paste these lines one at a time into a serial terminal (115200 baud)"]
    out += [f"{k}={v}    ; {c}" for k, v, c in settings(robot)]
    return "\n".join(out) + "\n"
