"""Turn a weld job (JSON) into a list of robot operations.

A job is a list of seams. For every seam the planner produces:

    rapid (joint move) -> approach point above the seam start
    straight approach  -> seam start
    arc on, start dwell
    weld path          -> sampled every `step` mm, optional weave, constant travel speed
    crater dwell, arc off
    straight retract

Vocabulary used below:
    u  seam travel direction (unit)
    n  "approach normal": points from the joint towards where the torch comes from
       (for a fillet it is the bisector of the two plate normals)
    w  lateral direction across the joint = n x u (weave goes along w)
    d  torch direction (points from the torch towards the work)
    travel angle  + = push (torch leans forward, wire points ahead), - = drag
    work angle offset  extra tilt of the torch across the joint, about u
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

DEFAULTS = {
    "speed": 6.0,              # travel speed along the seam, mm/s (MIG on thin steel: 4-10)
    "step": 1.0,               # path sampling, mm along the seam
    "travel_angle": 10.0,      # deg, push
    "work_angle_offset": 0.0,  # deg
    "standoff": 0.0,           # mm the TCP is held back from the joint along the torch axis
    "approach": 30.0,          # mm above the start, along the torch axis
    "retract": 30.0,           # mm
    "approach_speed": 15.0,    # mm/s
    "arc_start_dwell": 0.3,    # s
    "crater_dwell": 0.5,       # s
    "weave": None,             # {"pattern": "zigzag"|"sine", "amplitude": mm, "wavelength": mm}
}


# ---- operations -----------------------------------------------------------

@dataclass
class Rapid:
    """Joint-space move at full joint speed. Give either joints or a Cartesian pose."""
    joints: np.ndarray | None = None
    tip: np.ndarray | None = None
    direction: np.ndarray | None = None


@dataclass
class Linear:
    """Straight Cartesian step to this pose taking `dt` seconds (0 = as fast as the joints allow)."""
    tip: np.ndarray
    direction: np.ndarray
    dt: float
    weld: bool = False


@dataclass
class Arc:
    on: bool


@dataclass
class Dwell:
    seconds: float


@dataclass
class Comment:
    text: str


@dataclass
class Plan:
    name: str
    ops: list = field(default_factory=list)
    tool: float | None = None
    keep_out: list = field(default_factory=list)   # [{"name", "min": [x,y,z], "max": [x,y,z]}]
    clearance: float = 5.0                         # mm the wrist must stay away from keep-out boxes

    def weld_length(self) -> float:
        """Total length of TCP path travelled with the arc on (mm)."""
        total, prev = 0.0, None
        for op in self.ops:
            if isinstance(op, Linear):
                if op.weld and prev is not None:
                    total += float(np.linalg.norm(op.tip - prev))
                prev = op.tip
            elif isinstance(op, Rapid):
                prev = op.tip
        return total


# ---- helpers ----------------------------------------------------------------

def _unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < 1e-9:
        raise ValueError(f"zero-length vector {v}")
    return v / n


def _weave_offset(weave: dict | None, s: float) -> float:
    """Lateral offset (mm) at distance s along the seam. Starts and ends on the centreline."""
    if not weave:
        return 0.0
    amp = float(weave.get("amplitude", 0.0))
    lam = float(weave.get("wavelength", 4.0))
    x = s / lam
    pattern = weave.get("pattern", "zigzag")
    if pattern == "sine":
        return amp * np.sin(2 * np.pi * x)
    if pattern == "zigzag":
        return amp * (1.0 - 4.0 * abs(((x + 0.25) % 1.0) - 0.5))
    raise ValueError(f"unknown weave pattern '{pattern}' (use zigzag or sine)")


def torch_direction(u, n, travel_angle: float, work_angle_offset: float = 0.0) -> np.ndarray:
    u, n = _unit(u), _unit(n)
    n = _unit(n - np.dot(n, u) * u)          # make the normal perpendicular to the seam
    w = np.cross(n, u)
    phi, theta = np.radians(work_angle_offset), np.radians(travel_angle)
    across = -n * np.cos(phi) + w * np.sin(phi)
    return _unit(across * np.cos(theta) + u * np.sin(theta))


def _seam_normal(seam: dict, radial: np.ndarray | None = None, axis: np.ndarray | None = None):
    if "plates" in seam:                      # fillet: bisector of the plate normals
        a, b = (_unit(p) for p in seam["plates"])
        return _unit(a + b)
    normal = seam.get("normal", [0, 0, 1])
    if isinstance(normal, str):
        if radial is None:
            raise ValueError(f"normal '{normal}' only works on circle seams")
        modes = {"outside": radial, "inside": -radial, "axis": axis,
                 "fillet_outside": _unit(radial + axis), "fillet_inside": _unit(-radial + axis)}
        if normal not in modes:
            raise ValueError(f"unknown normal mode '{normal}'")
        return modes[normal]
    return _unit(normal)


# ---- seam samplers: yield (distance along seam, point, tangent, normal) -----

def _sample_line(seam, step):
    a, b = np.asarray(seam["start"], float), np.asarray(seam["end"], float)
    length = float(np.linalg.norm(b - a))
    u = _unit(b - a)
    n = _seam_normal(seam)
    count = max(1, int(np.ceil(length / step)))
    for i in range(count + 1):
        s = length * i / count
        yield s, a + u * s, u, n


def _sample_polyline(seam, step):
    pts = [np.asarray(p, float) for p in seam["points"]]
    n = _seam_normal(seam)
    s0 = 0.0
    for k in range(len(pts) - 1):
        sub = dict(seam, start=pts[k], end=pts[k + 1])
        for i, (s, p, u, _) in enumerate(_sample_line(sub, step)):
            if k > 0 and i == 0:
                continue
            yield s0 + s, p, u, n
        s0 += float(np.linalg.norm(pts[k + 1] - pts[k]))


def _sample_circle(seam, step):
    c = np.asarray(seam["center"], float)
    axis = _unit(seam.get("axis", [0, 0, 1]))
    radius = float(seam["radius"])
    ref = np.asarray(seam.get("start_direction", [1, 0, 0]), float)
    e1 = _unit(ref - np.dot(ref, axis) * axis)
    e2 = np.cross(axis, e1)
    start = np.radians(seam.get("start_angle", 0.0))
    sweep = np.radians(seam.get("sweep", 360.0))
    length = abs(sweep) * radius
    count = max(2, int(np.ceil(length / step)))
    sign = 1.0 if sweep >= 0 else -1.0
    for i in range(count + 1):
        a = start + sweep * i / count
        radial = np.cos(a) * e1 + np.sin(a) * e2
        u = sign * (-np.sin(a) * e1 + np.cos(a) * e2)
        yield length * i / count, c + radius * radial, u, _seam_normal(seam, radial, axis)


SAMPLERS = {"line": _sample_line, "polyline": _sample_polyline, "circle": _sample_circle}


# ---- planner -----------------------------------------------------------------

def _straight(p0, p1, d0, d1, speed, step, weld=False):
    """Linear ops from pose 0 to pose 1 (position and direction interpolated)."""
    dist = float(np.linalg.norm(p1 - p0))
    count = max(1, int(np.ceil(dist / step)))
    ops = []
    for i in range(1, count + 1):
        t = i / count
        ops.append(Linear(p0 + (p1 - p0) * t, _unit(d0 * (1 - t) + d1 * t),
                          dist / count / speed if speed > 0 else 0.0, weld))
    return ops


def _reorient(p, d0, d1, steps=12):
    """Turn the torch in place (used at polyline corners). Timed by the joint speed limits."""
    if np.dot(d0, d1) > 0.99999:
        return []
    return [Linear(p.copy(), _unit(d0 * (1 - t) + d1 * t), 0.0, True)
            for t in np.linspace(0, 1, steps + 1)[1:]]


def plan_seam(seam: dict, defaults: dict) -> list:
    cfg = {**DEFAULTS, **defaults, **seam}
    kind = seam.get("type", "line")
    if kind not in SAMPLERS:
        raise ValueError(f"unknown seam type '{kind}' (use {', '.join(SAMPLERS)})")
    weave = cfg["weave"]
    step = float(cfg["step"])
    if weave:
        step = min(step, float(weave.get("wavelength", 4.0)) / 8.0)

    path = []    # (seam distance, tcp, torch dir)
    for s, p, u, n in SAMPLERS[kind](cfg, step):
        d = torch_direction(u, n, cfg["travel_angle"], cfg["work_angle_offset"])
        w = _unit(np.cross(_unit(n - np.dot(n, u) * u), u))
        tcp = p + w * _weave_offset(weave, s) - d * cfg["standoff"]
        path.append((s, tcp, d))

    ops = [Comment(f"seam: {seam.get('name', kind)}")]
    s0, p0, d0 = path[0]
    above = p0 - d0 * cfg["approach"]
    ops.append(Rapid(tip=above, direction=d0))
    ops += _straight(above, p0, d0, d0, cfg["approach_speed"], 2.0)
    ops += [Arc(True), Dwell(cfg["arc_start_dwell"])]
    speed = float(cfg["speed"])
    for (sa, pa, da), (sb, pb, db) in zip(path, path[1:]):
        if np.dot(da, db) < 0.996:            # sharp turn (> ~5 deg): reorient on the spot
            ops += _reorient(pa, da, db)
        ops.append(Linear(pb, db, (sb - sa) / speed, True))
    ops += [Dwell(cfg["crater_dwell"]), Arc(False)]
    s1, p1, d1 = path[-1]
    ops += _straight(p1, p1 - d1 * cfg["retract"], d1, d1, cfg["approach_speed"], 2.0)
    return ops


def plan_job(job: dict) -> Plan:
    plan = Plan(name=job.get("name", "job"), tool=job.get("tool_length"),
                keep_out=job.get("keep_out", []), clearance=job.get("clearance", 5.0))
    defaults = job.get("defaults", {})
    for seam in job["seams"]:
        plan.ops += plan_seam(seam, defaults)
    plan.ops.append(Comment("back to the safe pose"))
    plan.ops.append(Rapid(joints=np.asarray(job["safe_pose"], float) if "safe_pose" in job else None))
    return plan


def load_job(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())
