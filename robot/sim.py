"""Matplotlib previews: a still image of a weld job and an animated GIF of the robot running it."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

from .config import Robot  # noqa: E402
from .gcode import Trajectory, tcp_path  # noqa: E402
from .kinematics import fk  # noqa: E402

LINK_COLOR = "#3b6ea5"
TOOL_COLOR = "#e07b24"
WELD_COLOR = "#d62728"
TRAVEL_COLOR = "#9a9a9a"


def _setup(ax, title: str):
    ax.set_xlim(-150, 350)
    ax.set_ylim(-250, 250)
    ax.set_zlim(0, 420)
    ax.set_box_aspect((500, 500, 420))
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title(title)
    xx, yy = np.meshgrid(np.linspace(-150, 350, 2), np.linspace(-250, 250, 2))
    ax.plot_surface(xx, yy, np.zeros_like(xx), color="#dddddd", alpha=0.25, linewidth=0)
    t = np.linspace(0, 2 * np.pi, 40)
    for z in (0, 155):
        ax.plot(85 * np.cos(t), 85 * np.sin(t), z, color="#555555", linewidth=1)


def draw_robot(ax, robot: Robot, q, alpha: float = 1.0):
    """Stick model of the arm. Returns the matplotlib artists so they can be updated."""
    p = fk(robot, q).points
    chain = np.array([[0, 0, 155], p["shoulder"], p["elbow"], p["wrist"]])
    arm, = ax.plot(chain[:, 0], chain[:, 1], chain[:, 2], "-o", color=LINK_COLOR,
                   linewidth=6, markersize=8, alpha=alpha, solid_capstyle="round")
    tool = np.array([p["wrist"], p["tip"]])
    torch, = ax.plot(tool[:, 0], tool[:, 1], tool[:, 2], "-", color=TOOL_COLOR,
                     linewidth=4, alpha=alpha)
    return arm, torch


def _draw_path(ax, pts, weld):
    ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], "--", color=TRAVEL_COLOR, linewidth=0.8)
    w = np.where(weld, 1.0, np.nan)
    ax.plot(pts[:, 0] * w, pts[:, 1] * w, pts[:, 2] * w, "-", color=WELD_COLOR, linewidth=2)


def save_png(traj: Trajectory, path: str):
    robot = traj.robot
    pts, weld = tcp_path(traj)
    qs = traj.joint_path()
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(projection="3d")
    _setup(ax, f"{traj.name}")
    _draw_path(ax, pts, weld)
    weld_idx = np.flatnonzero(weld)
    picks = [weld_idx[0], weld_idx[len(weld_idx) // 2], weld_idx[-1]] if len(weld_idx) else [0]
    for k, i in enumerate(picks):
        draw_robot(ax, robot, qs[i], alpha=0.35 + 0.3 * k)
    ax.view_init(elev=22, azim=-60)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def save_gif(traj: Trajectory, path: str, frames: int = 120, fps: int = 20):
    robot = traj.robot
    pts, weld = tcp_path(traj)
    qs = traj.joint_path()
    idx = np.unique(np.linspace(0, len(qs) - 1, min(frames, len(qs))).astype(int))
    fig = plt.figure(figsize=(6.4, 5.6))
    ax = fig.add_subplot(projection="3d")
    _setup(ax, traj.name)
    ax.view_init(elev=22, azim=-60)
    trail, = ax.plot([], [], [], "-", color=WELD_COLOR, linewidth=2)
    arm, torch = draw_robot(ax, robot, qs[0])
    spark, = ax.plot([], [], [], "*", color="#ffcc00", markersize=14)

    def update(frame):
        i = idx[frame]
        p = fk(robot, qs[i]).points
        chain = np.array([[0, 0, 155], p["shoulder"], p["elbow"], p["wrist"]])
        arm.set_data_3d(chain[:, 0], chain[:, 1], chain[:, 2])
        torch.set_data_3d([p["wrist"][0], p["tip"][0]], [p["wrist"][1], p["tip"][1]],
                          [p["wrist"][2], p["tip"][2]])
        done = np.where(weld[: i + 1], 1.0, np.nan)
        trail.set_data_3d(pts[: i + 1, 0] * done, pts[: i + 1, 1] * done, pts[: i + 1, 2] * done)
        if weld[i]:
            spark.set_data_3d([p["tip"][0]], [p["tip"][1]], [p["tip"][2]])
        else:
            spark.set_data_3d([], [], [])
        return arm, torch, trail, spark

    anim = FuncAnimation(fig, update, frames=len(idx), interval=1000 / fps, blit=False)
    anim.save(path, writer=PillowWriter(fps=fps))
    plt.close(fig)
