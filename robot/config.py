"""Load the robot description (geometry, joints, motors, masses) from config/robot.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "robot.json"


@dataclass(frozen=True)
class Motor:
    working_nm: float
    full_steps: int
    gearbox_efficiency: float
    gearbox_max_nm: float


@dataclass(frozen=True)
class Joint:
    name: str
    axis: str            # G-code axis letter used by the firmware (X, Y, Z, A, B)
    min: float           # degrees
    max: float           # degrees
    motor: Motor
    gear_ratio: float
    microsteps: int
    max_speed: float     # deg/s
    accel: float         # deg/s^2
    home: float          # joint angle (deg) right after the homing cycle finishes

    @property
    def steps_per_degree(self) -> float:
        return self.motor.full_steps * self.microsteps * self.gear_ratio / 360.0

    @property
    def output_torque_nm(self) -> float:
        """Usable torque at the joint output, capped by the gearbox rating."""
        geared = self.motor.working_nm * self.gear_ratio * self.motor.gearbox_efficiency
        return min(geared, self.motor.gearbox_max_nm)

    def in_range(self, angle: float, margin: float = 0.0) -> bool:
        return self.min + margin <= angle <= self.max - margin


@dataclass(frozen=True)
class Mass:
    name: str
    kg: float
    link: int
    at: float


@dataclass(frozen=True)
class Robot:
    name: str
    d1: float
    l2: float
    l3: float
    tool: float
    joints: tuple[Joint, ...]
    masses: tuple[Mass, ...] = field(default_factory=tuple)
    dynamic_factor: float = 1.5
    ready_pose: tuple[float, ...] = (0, 0, 0, 0, 0)

    @property
    def axes(self) -> str:
        return "".join(j.axis for j in self.joints)

    def with_tool(self, tool: float) -> "Robot":
        """Same robot with a different tool length (e.g. pen vs. dummy torch)."""
        return Robot(self.name, self.d1, self.l2, self.l3, tool, self.joints,
                     self.masses, self.dynamic_factor, self.ready_pose)


def load(path: str | Path | None = None) -> Robot:
    data = json.loads(Path(path or DEFAULT_CONFIG).read_text())
    motors = {k: Motor(**v) for k, v in data["motors"].items() if not k.startswith("_")}
    joints = tuple(
        Joint(name=j["name"], axis=j["axis"], min=j["min"], max=j["max"],
              motor=motors[j["motor"]], gear_ratio=j["gear_ratio"],
              microsteps=j["microsteps"], max_speed=j["max_speed"],
              accel=j["accel"], home=j["home"])
        for j in data["joints"]
    )
    masses = tuple(Mass(**m) for m in data.get("masses", {}).get("items", []))
    g = data["geometry"]
    return Robot(
        name=data.get("name", "robot"),
        d1=g["d1"], l2=g["l2"], l3=g["l3"], tool=g["tool"],
        joints=joints,
        masses=masses,
        dynamic_factor=data.get("masses", {}).get("dynamic_factor", 1.5),
        ready_pose=tuple(data.get("ready_pose", [0] * len(joints))),
    )
