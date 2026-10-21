"""Forward and inverse kinematics for the 5-axis welding arm.

Joint layout (industrial 6-axis arm without the last roll, because a round
torch does not need to spin about its own axis):

    J1  base yaw        about world Z
    J2  shoulder pitch  0 = upper arm vertical, + leans forward
    J3  elbow pitch     0 = forearm at 90 deg to upper arm, + bends down
    J4  forearm roll    about the forearm axis
    J5  wrist pitch     0 = tool at 90 deg to forearm (points down when forearm is level)

J4 and J5 axes intersect at the wrist centre and the tool axis passes through
it, so position (J1-J3) and torch direction (J4-J5) decouple and the inverse
kinematics is closed-form.

Coordinates: origin at the centre of the base on the table, Z up, X forward
at J1 = 0. Lengths in mm, angles in degrees at the public API.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Robot


class Unreachable(ValueError):
    """The requested pose is outside the workspace or the joint limits."""


def _rx(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


@dataclass
class Pose:
    tip: np.ndarray          # TCP position (mm)
    direction: np.ndarray    # unit vector the torch points along (towards the work)
    points: dict             # joint centres for drawing: base, shoulder, elbow, wrist, tip
    tool_frame: np.ndarray   # 3x3 rotation of the tool flange


def fk(robot: Robot, q_deg) -> Pose:
    q1, q2, q3, q4, q5 = np.radians(np.asarray(q_deg, dtype=float))
    shoulder = np.array([0.0, 0.0, robot.d1])
    r1 = _rz(q1)
    elbow = shoulder + r1 @ _ry(q2) @ np.array([0.0, 0.0, robot.l2])
    r3 = r1 @ _ry(q2 + q3)
    wrist = elbow + r3 @ np.array([robot.l3, 0.0, 0.0])
    r5 = r3 @ _rx(q4) @ _ry(q5)
    direction = r5 @ np.array([0.0, 0.0, -1.0])
    tip = wrist + robot.tool * direction
    points = {"base": np.zeros(3), "shoulder": shoulder, "elbow": elbow,
              "wrist": wrist, "tip": tip}
    return Pose(tip=tip, direction=direction, points=points, tool_frame=r5)


def _wrap180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def ik(robot: Robot, tip, direction, seed=None, check_limits: bool = True) -> np.ndarray:
    """Joint angles (deg) that put the TCP at `tip` with the torch pointing along `direction`.

    `seed` (previous joint angles) picks the wrist solution closest to the
    current pose so long paths stay continuous.
    """
    tip = np.asarray(tip, dtype=float)
    d = np.asarray(direction, dtype=float)
    norm = np.linalg.norm(d)
    if norm < 1e-9:
        raise ValueError("torch direction must be non-zero")
    d = d / norm
    seed = None if seed is None else np.asarray(seed, dtype=float)

    # Wrist centre sits one tool length back along the torch axis.
    w = tip - robot.tool * d
    r = np.hypot(w[0], w[1])
    if r < 1e-6:
        if seed is None:
            raise Unreachable("wrist centre is on the base axis (J1 singularity)")
        q1 = np.radians(seed[0])
    else:
        q1 = np.arctan2(w[1], w[0])

    h = w[2] - robot.d1
    l2, l3 = robot.l2, robot.l3
    c = (r * r + h * h - l2 * l2 - l3 * l3) / (2 * l2 * l3)
    if c > 1.0 or c < -1.0:
        dist = np.hypot(r, h)
        raise Unreachable(f"wrist centre {np.round(w, 1).tolist()} is {dist:.0f} mm from the "
                          f"shoulder; reachable range is {abs(l2 - l3):.0f}-{l2 + l3:.0f} mm")
    gamma = -np.arccos(c)                                   # elbow-up branch
    alpha = np.arctan2(h, r) - np.arctan2(l3 * np.sin(gamma), l2 + l3 * np.cos(gamma))
    q2 = np.pi / 2 - alpha
    s = -(alpha + gamma)                                    # forearm pitch below horizontal
    q3 = s - q2

    # Torch direction expressed in the forearm frame.
    dl = (_rz(q1) @ _ry(s)).T @ d
    q5 = -np.arcsin(np.clip(dl[0], -1.0, 1.0))
    if np.cos(q5) > 1e-6:
        q4 = np.arctan2(dl[1], -dl[2])
    else:   # torch parallel to the forearm: J4 is free, keep it where it was
        q4 = np.radians(seed[3]) if seed is not None else 0.0

    q1d, q2d, q3d, q4d, q5d = np.degrees([q1, q2, q3, q4, q5])
    j = robot.joints
    if check_limits:
        for idx, val in enumerate((q1d, q2d, q3d)):
            if not j[idx].in_range(val):
                raise Unreachable(f"{j[idx].name} would need {val:.1f} deg "
                                  f"(limit {j[idx].min}..{j[idx].max})")

    # Two wrist solutions (flip), each with +/-360 deg roll variants.
    candidates = []
    for a4, a5 in ((q4d, q5d), (q4d + 180.0, _wrap180(180.0 - q5d))):
        a4 = _wrap180(a4)
        for k in (-360.0, 0.0, 360.0):
            candidates.append((a4 + k, a5))
    if check_limits:
        candidates = [(a4, a5) for a4, a5 in candidates
                      if j[3].in_range(a4) and j[4].in_range(a5)]
        if not candidates:
            raise Unreachable("torch direction needs J4/J5 outside their limits")

    if seed is not None:
        best = min(candidates, key=lambda c4: abs(c4[0] - seed[3]) + abs(c4[1] - seed[4]))
    else:
        best = min(candidates, key=lambda c4: abs(c4[0]) + abs(c4[1]))
    return np.array([q1d, q2d, q3d, best[0], best[1]])
