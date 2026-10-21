import numpy as np

from robot import config, statics

ROBOT = config.load()


def test_shoulder_torque_is_largest_with_arm_stretched_level():
    level = statics.gravity_torques(ROBOT, [0, 90, -80, 0, 0])
    upright = statics.gravity_torques(ROBOT, [0, 0, -80, 0, 0])
    assert abs(level[1]) > abs(upright[1])


def test_no_gravity_torque_on_base_yaw():
    assert statics.gravity_torques(ROBOT, [30, 40, 10, 20, 30])[0] == 0


def test_default_motors_pass():
    _, ok = statics.report(ROBOT)
    assert ok
