from pathlib import Path

import numpy as np
import pytest

from robot import config, gcode, weld
from robot.weld import Arc, Linear, torch_direction

ROBOT = config.load()
JOBS = sorted((Path(__file__).resolve().parent.parent / "jobs").glob("*.json"))


def test_torch_direction_push_angle():
    d = torch_direction(u=[1, 0, 0], n=[0, 0, 1], travel_angle=10)
    assert np.isclose(np.degrees(np.arcsin(d[0])), 10)    # leans forward = push
    assert d[2] < 0                                       # points down at the work


def test_fillet_bisector_is_45_degrees():
    job = {"seams": [{"type": "line", "start": [250, 0, 100], "end": [180, 0, 100],
                      "plates": [[0, 0, 1], [0, -1, 0]], "travel_angle": 0}]}
    ops = weld.plan_job(job).ops
    d = next(op.direction for op in ops if isinstance(op, Linear) and op.weld)
    assert np.allclose(d, [0, np.sqrt(0.5), -np.sqrt(0.5)])


def test_travel_speed_is_respected():
    job = {"seams": [{"type": "line", "start": [270, 0, 100], "end": [170, 0, 100],
                      "normal": [0, 0, 1], "speed": 5}]}
    ops = weld.plan_job(job).ops
    weld_time = sum(op.dt for op in ops if isinstance(op, Linear) and op.weld)
    assert weld_time == pytest.approx(100 / 5)


def test_weave_stays_within_amplitude():
    job = {"seams": [{"type": "line", "start": [270, 0, 100], "end": [170, 0, 100],
                      "normal": [0, 0, 1], "weave": {"pattern": "zigzag", "amplitude": 2,
                                                     "wavelength": 4}}]}
    ys = [op.tip[1] for op in weld.plan_job(job).ops if isinstance(op, Linear) and op.weld]
    assert max(ys) == pytest.approx(2, abs=1e-6)
    assert min(ys) == pytest.approx(-2, abs=1e-6)


def test_arc_switches_on_once_and_off_once_per_seam():
    job = weld.load_job(JOBS[0])
    ops = weld.plan_job(job).ops
    arcs = [op.on for op in ops if isinstance(op, Arc)]
    assert arcs == [True, False] * len(job["seams"])


@pytest.mark.parametrize("path", JOBS, ids=lambda p: p.stem)
def test_example_jobs_plan_and_respect_limits(path):
    traj = gcode.solve(weld.plan_job(weld.load_job(path)), ROBOT)
    q = traj.joint_path()
    for i, j in enumerate(ROBOT.joints):
        assert q[:, i].min() >= j.min and q[:, i].max() <= j.max
    assert not traj.warnings


def test_dry_run_never_emits_m8():
    traj = gcode.solve(weld.plan_job(weld.load_job(JOBS[0])), ROBOT)
    dry = gcode.to_gcode(traj, ROBOT, arc_enabled=False)
    live = gcode.to_gcode(traj, ROBOT, arc_enabled=True)
    assert not any(line.startswith("M8") for line in dry.splitlines())
    assert any(line.startswith("M8") for line in live.splitlines())
    assert "G93" in live


def test_inverse_time_feed_matches_step_time():
    traj = gcode.solve(weld.plan_job(weld.load_job(JOBS[0])), ROBOT)
    text = gcode.to_gcode(traj, ROBOT)
    moves = [s for s in traj.steps if s.kind == "move"]
    feeds = [float(line.rsplit("F", 1)[1]) for line in text.splitlines() if line.startswith("G1")]
    assert len(feeds) == len(moves)
    assert all(np.isclose(f, 60 / m.dt, rtol=1e-3) for f, m in zip(feeds, moves))
