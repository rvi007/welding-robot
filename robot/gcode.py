"""Solve a weld plan into joint angles and write G-code for grbl-Mega-5X.

The firmware treats every joint as an axis measured in degrees
(X=J1, Y=J2, Z=J3, A=J4, B=J5). Cartesian straight lines are produced here by
sampling the path finely and solving the inverse kinematics for each sample.
Each sample is sent as one G1 move in inverse-time mode (G93), so the torch
keeps the programmed travel speed no matter how far each joint has to turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .collision import first_hit
from .config import Robot
from .kinematics import Unreachable, fk, ik
from .weld import Arc, Comment, Dwell, Linear, Plan, Rapid

MAX_JUMP_DEG = 15.0   # more than this between two path samples means a flip/singularity


class PlanError(ValueError):
    pass


@dataclass
class Step:
    kind: str                    # rapid | move | arc | dwell | comment
    q: np.ndarray | None = None
    dt: float = 0.0
    weld: bool = False
    value: object = None


@dataclass
class Trajectory:
    name: str
    robot: Robot
    steps: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def duration(self, robot: Robot) -> float:
        total, q = 0.0, np.asarray(robot.ready_pose, float)
        vmax = np.array([j.max_speed for j in robot.joints])
        for st in self.steps:
            if st.kind == "rapid":
                total += float(np.max(np.abs(st.q - q) / vmax)) + 0.2
                q = st.q
            elif st.kind == "move":
                total += st.dt
                q = st.q
            elif st.kind == "dwell":
                total += st.value
        return total

    def joint_path(self) -> np.ndarray:
        return np.array([st.q for st in self.steps if st.q is not None])


def solve(plan: Plan, robot: Robot) -> Trajectory:
    if plan.tool:
        robot = robot.with_tool(plan.tool)
    traj = Trajectory(plan.name, robot)
    q = np.asarray(robot.ready_pose, float)
    vmax = np.array([j.max_speed for j in robot.joints])
    slowed = 0

    for op in plan.ops:
        if isinstance(op, Comment):
            traj.steps.append(Step("comment", value=op.text))
        elif isinstance(op, Arc):
            traj.steps.append(Step("arc", value=op.on))
        elif isinstance(op, Dwell):
            traj.steps.append(Step("dwell", value=float(op.seconds)))
        elif isinstance(op, Rapid):
            if op.joints is not None:
                target = np.asarray(op.joints, float)
            elif op.tip is not None:
                try:
                    target = ik(robot, op.tip, op.direction, seed=q)
                except Unreachable as e:
                    raise PlanError(f"cannot reach approach point {np.round(op.tip, 1).tolist()}: {e}")
            else:
                target = np.asarray(robot.ready_pose, float)
            hit = first_hit(robot, target, plan.keep_out, plan.clearance)
            if hit:
                raise PlanError(f"approach pose collides: {hit}")
            traj.steps.append(Step("rapid", q=target))
            q = target
        elif isinstance(op, Linear):
            try:
                target = ik(robot, op.tip, op.direction, seed=q)
            except Unreachable as e:
                raise PlanError(f"path point {np.round(op.tip, 1).tolist()} unreachable: {e}")
            delta = np.abs(target - q)
            if np.max(delta) > MAX_JUMP_DEG:
                j = int(np.argmax(delta))
                raise PlanError(
                    f"{robot.joints[j].name} jumps {delta[j]:.0f} deg near "
                    f"{np.round(op.tip, 1).tolist()} (wrist flip or singularity). "
                    "Change the travel/work angle or move the part.")
            hit = first_hit(robot, target, plan.keep_out, plan.clearance)
            if hit:
                raise PlanError(f"collision near {np.round(op.tip, 1).tolist()}: {hit}. "
                                "Turn or move the part, or change the torch angles.")
            dt_min = float(np.max(delta / vmax))
            dt = op.dt
            if dt <= 0:
                dt = max(dt_min * 1.1, 0.01)
            elif dt < dt_min:
                if op.weld:
                    slowed += 1
                dt = dt_min
            traj.steps.append(Step("move", q=target, dt=dt, weld=op.weld))
            q = target
    if slowed:
        traj.warnings.append(
            f"{slowed} weld segment(s) slowed below the programmed travel speed because a joint "
            "hit its speed limit; expect a heavier bead there.")
    return traj


def _axes(robot: Robot, q) -> str:
    return " ".join(f"{j.axis}{v:.3f}" for j, v in zip(robot.joints, q))


def to_gcode(traj: Trajectory, robot: Robot, arc_enabled: bool = False) -> str:
    lines = [
        f"; Ravi WR-1 program: {traj.name}",
        "; joint-space G-code for grbl-Mega-5X, axes in degrees: "
        + ", ".join(f"{j.axis}={j.name}" for j in robot.joints),
        f"; arc output: {'ENABLED (M8 drives the arc relay)' if arc_enabled else 'dry run (no M8)'}",
        f"; estimated run time: {traj.duration(robot):.0f} s",
        "G90 G94",
        "M9",
        f"G0 {_axes(robot, robot.ready_pose)}",
        "G93",
    ]
    for st in traj.steps:
        if st.kind == "comment":
            lines.append(f"; {st.value}")
        elif st.kind == "rapid":
            lines.append(f"G0 {_axes(robot, st.q)}")
        elif st.kind == "move":
            lines.append(f"G1 {_axes(robot, st.q)} F{60.0 / st.dt:.2f}")
        elif st.kind == "dwell":
            if st.value > 0:
                lines.append(f"G4 P{st.value:.2f}")
        elif st.kind == "arc":
            if arc_enabled:
                lines.append("M8 ; ARC ON" if st.value else "M9 ; ARC OFF")
            else:
                lines.append(f"; ARC {'ON' if st.value else 'OFF'} (dry run)")
    lines += ["M9", "G94", "M2", ""]
    return "\n".join(lines)


def tcp_path(traj: Trajectory) -> tuple[np.ndarray, np.ndarray]:
    """TCP positions along the trajectory and a mask of which samples are welding."""
    pts, weld = [], []
    for st in traj.steps:
        if st.q is not None:
            pts.append(fk(traj.robot, st.q).tip)
            weld.append(st.weld)
    return np.array(pts), np.array(weld, dtype=bool)
