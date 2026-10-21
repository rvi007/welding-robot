import numpy as np
import pytest

from robot import config
from robot.kinematics import Unreachable, fk, ik

ROBOT = config.load()


def test_ready_pose_geometry():
    p = fk(ROBOT, [0, 0, 0, 0, 0])
    # upper arm straight up, forearm level, torch straight down
    assert np.allclose(p.points["elbow"], [0, 0, ROBOT.d1 + ROBOT.l2])
    assert np.allclose(p.points["wrist"], [ROBOT.l3, 0, ROBOT.d1 + ROBOT.l2])
    assert np.allclose(p.direction, [0, 0, -1])
    assert np.allclose(p.tip, [ROBOT.l3, 0, ROBOT.d1 + ROBOT.l2 - ROBOT.tool])


def test_ik_inverts_fk_over_random_poses():
    rng = np.random.default_rng(1)
    checked = 0
    for _ in range(3000):
        q = [rng.uniform(j.min + 1, j.max - 1) for j in ROBOT.joints]
        q[4] = rng.uniform(-80, 80)          # stay away from the wrist singularity
        p = fk(ROBOT, q)
        try:
            q2 = ik(ROBOT, p.tip, p.direction, seed=q)
        except Unreachable:
            continue                          # elbow-down poses are out of scope
        p2 = fk(ROBOT, q2)
        assert np.allclose(p2.tip, p.tip, atol=1e-6)
        assert np.allclose(p2.direction, p.direction, atol=1e-6)
        checked += 1
    assert checked > 1000


def test_out_of_reach_raises():
    with pytest.raises(Unreachable):
        ik(ROBOT, [1000, 0, 0], [0, 0, -1])


def test_seed_keeps_wrist_continuous():
    q_prev = ik(ROBOT, [230, 0, 100], [0, 0.707, -0.707])
    q_next = ik(ROBOT, [231, 0, 100], [0, 0.707, -0.707], seed=q_prev)
    assert np.max(np.abs(q_next - q_prev)) < 2.0
