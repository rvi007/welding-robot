"""Gravity torque check: is each joint motor strong enough over the whole workspace?"""

from __future__ import annotations

import itertools

import numpy as np

from .config import Robot
from .kinematics import _rx, _ry, _rz, fk

G = 9.81


def gravity_torques(robot: Robot, q_deg) -> np.ndarray:
    """Static torque (N*m) each joint must hold at pose q. J1 is always 0 (vertical axis)."""
    q1, q2, q3, q4, q5 = np.radians(q_deg)
    pose = fk(robot, q_deg)
    sh, el, wr = pose.points["shoulder"], pose.points["elbow"], pose.points["wrist"]
    r1 = _rz(q1)
    r2 = r1 @ _ry(q2)
    r3 = r1 @ _ry(q2 + q3)
    r4 = r3 @ _rx(q4)

    masses = []   # (link, position mm, kg)
    for m in robot.masses:
        if m.link == 2:
            p = sh + r2 @ np.array([0, 0, m.at])
        elif m.link == 3:
            p = el + r3 @ np.array([m.at, 0, 0])
        else:
            p = wr + pose.direction * m.at
        masses.append((m.link, p, m.kg))

    # (joint index, point on axis, axis direction, links it carries)
    axes = [
        (1, sh, r1 @ np.array([0, 1, 0]), (2, 3, 5)),
        (2, el, r1 @ np.array([0, 1, 0]), (3, 5)),
        (3, wr, r3 @ np.array([1, 0, 0]), (5,)),
        (4, wr, r4 @ np.array([0, 1, 0]), (5,)),
    ]
    tau = np.zeros(5)
    weight = np.array([0, 0, -G])
    for idx, origin, axis, links in axes:
        for link, p, kg in masses:
            if link in links:
                tau[idx] += np.dot(np.cross((p - origin) / 1000.0, kg * weight), axis)
    return tau


def worst_case(robot: Robot, samples: int = 9) -> np.ndarray:
    """Largest |gravity torque| per joint over a grid of poses inside the joint limits."""
    j = robot.joints
    grids = [np.linspace(j[i].min, j[i].max, samples) for i in (1, 2, 4)]
    q4s = np.linspace(-90, 90, 5)
    worst = np.zeros(5)
    for q2, q3, q5 in itertools.product(*grids):
        for q4 in q4s:
            worst = np.maximum(worst, np.abs(gravity_torques(robot, [0, q2, q3, q4, q5])))
    return worst


def report(robot: Robot) -> tuple[str, bool]:
    worst = worst_case(robot)
    rows = ["joint               gravity  x{:.1f} need  available  status".format(robot.dynamic_factor),
            "------------------  -------  ----------  ---------  ------"]
    ok = True
    for jt, g in zip(robot.joints, worst):
        need = g * robot.dynamic_factor
        have = jt.output_torque_nm
        good = have >= need
        ok &= good
        label = "OK" if good else "UPGRADE"
        if jt.axis == "X":
            label, need_s = "OK*", "   (inertia)"
        else:
            need_s = f"{need:8.2f} Nm"
        rows.append(f"{jt.name:<18}  {g:5.2f} Nm  {need_s:>10}  {have:6.2f} Nm  {label}")
    rows.append("* J1 turns about a vertical axis, so gravity puts no torque on it; "
                "it is sized for acceleration.")
    return "\n".join(rows), ok
