"""Clearance check between the robot's wrist end and keep-out boxes (work block, plates, fixtures).

The arm itself is not modelled in detail. The parts that actually come near the work
are checked: the J5 motor hanging off the side of the wrist, the wrist hub, and the
front of the forearm (J4 motor). Each is sampled as a grid of points on its box.
Dimensions match cad/config.scad and cad/vitamins.scad.
"""

from __future__ import annotations

import itertools

import numpy as np

from .config import Robot
from .kinematics import _rx, _ry, _rz, fk

# (name, frame, box min, box max) in mm; frame "wrist" = after J4, origin at the wrist centre,
# "forearm" = forearm frame with origin at the wrist centre (X along the forearm).
BODIES = [
    ("J5 motor",      "wrist",   (-22, -79, -22), (22, -12, 22)),
    ("wrist hub",     "wrist",   (-32, -12, -12), (-17, 12, 12)),
    ("forearm front", "forearm", (-100, -24, -28), (-32, 24, 28)),
]


def _grid(lo, hi, n=4):
    axes = [np.linspace(a, b, n) for a, b in zip(lo, hi)]
    return np.array(list(itertools.product(*axes)))


_GRIDS = [(name, frame, _grid(lo, hi)) for name, frame, lo, hi in BODIES]


def body_points(robot: Robot, q) -> dict[str, np.ndarray]:
    q1, q2, q3, q4, _ = np.radians(q)
    wrist = fk(robot, q).points["wrist"]
    r3 = _rz(q1) @ _ry(q2 + q3)
    frames = {"forearm": r3, "wrist": r3 @ _rx(q4)}
    return {name: wrist + pts @ frames[frame].T for name, frame, pts in _GRIDS}


def first_hit(robot: Robot, q, boxes, margin: float = 5.0):
    """Name of the first body inside a keep-out box (grown by `margin`), or None."""
    if not boxes:
        return None
    pts = body_points(robot, q)
    for box in boxes:
        lo = np.asarray(box["min"], float) - margin
        hi = np.asarray(box["max"], float) + margin
        for name, p in pts.items():
            if np.any(np.all((p >= lo) & (p <= hi), axis=1)):
                return f"{name} within {margin:g} mm of '{box.get('name', 'keep-out box')}'"
    return None
