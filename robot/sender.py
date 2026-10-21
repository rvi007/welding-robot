"""Talk to grbl-Mega-5X over USB serial: home, jog, stream programs, stop."""

from __future__ import annotations

import time

from .config import Robot


class GrblError(RuntimeError):
    pass


class Grbl:
    def __init__(self, port: str, baud: int = 115200):
        import serial  # pyserial; imported here so the rest of the toolkit works without it

        self.ser = serial.Serial(port, baud, timeout=0.2)
        self.ser.write(b"\r\n\r\n")
        time.sleep(2.0)                  # the Mega resets when the port opens
        self.ser.reset_input_buffer()

    def close(self):
        self.ser.close()

    def _readline(self) -> str:
        return self.ser.readline().decode(errors="replace").strip()

    def command(self, line: str, timeout: float = 30.0) -> list[str]:
        """Send one line and wait for 'ok'. Raises on 'error:' or 'ALARM:'."""
        self.ser.write((line.strip() + "\n").encode())
        replies, end = [], time.time() + timeout
        while time.time() < end:
            msg = self._readline()
            if not msg:
                continue
            if msg == "ok":
                return replies
            if msg.startswith("error") or msg.startswith("ALARM"):
                raise GrblError(f"{line!r} -> {msg}")
            replies.append(msg)
        raise GrblError(f"timeout waiting for reply to {line!r}")

    def status(self) -> str:
        self.ser.write(b"?")
        end = time.time() + 2
        while time.time() < end:
            msg = self._readline()
            if msg.startswith("<"):
                return msg
        return "(no status)"

    def wait_idle(self, timeout: float = 600):
        end = time.time() + timeout
        while time.time() < end:
            if self.status().startswith("<Idle"):
                return
            time.sleep(0.2)
        raise GrblError("robot did not become idle")

    def stop(self):
        """Feed hold, then soft reset. Reset also switches the arc output (M8) off."""
        self.ser.write(b"!")
        time.sleep(0.3)
        self.ser.write(b"\x18")

    def home(self, robot: Robot):
        """Run the homing cycle, then tell grbl the joint angles at the homed pose."""
        self.command("$H", timeout=180)
        axes = " ".join(f"{j.axis}{j.home:.3f}" for j in robot.joints)
        self.command(f"G10 L20 P1 {axes}")
        self.command("G90 G94")

    def move_joints(self, robot: Robot, q):
        axes = " ".join(f"{j.axis}{v:.3f}" for j, v in zip(robot.joints, q))
        self.command("G90 G94")
        self.command(f"G0 {axes}")
        self.wait_idle()

    def stream(self, lines, progress=None):
        """Simple send-and-wait streaming; plenty fast for 1 mm path steps."""
        lines = [ln.split(";", 1)[0].strip() for ln in lines]
        lines = [ln for ln in lines if ln]
        for i, line in enumerate(lines, 1):
            self.command(line, timeout=120)
            if progress:
                progress(i, len(lines), line)
        self.wait_idle()
