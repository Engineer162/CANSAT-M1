"""
CANSAT Sensor Data Monitor
Reads sensor data from an Arduino over serial and plots it live.
"""

import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import re
import sys
import logging

# ─── Configuration ──────────────────────────────────────────────────────────

ARDUINO_PORT = "/dev/ttyACM3"   # Change to your port (e.g. "COM3" on Windows)
BAUD_RATE = 9600
MAX_POINTS = 100                # Rolling window size
PLOT_INTERVAL_MS = 500          # How often (ms) the plot refreshes

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Sensor parsing ─────────────────────────────────────────────────────────

# Pre-compile every regex once at module load — avoids recompiling each frame.
SENSOR_PATTERNS: dict[str, re.Pattern] = {
    "pressure":         re.compile(r"Pressure:\s*([\d.]+)\s*Pa"),
    "raw_altitude":     re.compile(r"Raw altitude:\s*([-\d.]+)\s*m"),
    "filtered_altitude":re.compile(r"Filtered altitude:\s*([-\d.]+)\s*m"),
    "mpu_temp":         re.compile(r"MPU Temp:\s*([\d.]+)\s*C"),
}

SENSOR_KEYS = list(SENSOR_PATTERNS.keys())


def parse_sensor_data(line: str) -> tuple[str | None, float | None]:
    """Return (key, value) for the first pattern that matches, or (None, None)."""
    for key, pattern in SENSOR_PATTERNS.items():
        match = pattern.search(line)
        if match:
            return key, float(match.group(1))
    return None, None


# ─── Serial reader ──────────────────────────────────────────────────────────


class SerialReader:
    """Manages the serial connection and feeds parsed values into deques."""

    def __init__(self, port: str, baud: int, max_points: int):
        self.port = port
        self.baud = baud
        self.ser: serial.Serial | None = None

        # One deque per sensor key, shared with the plotter.
        self.data: dict[str, deque] = {
            key: deque(maxlen=max_points) for key in SENSOR_KEYS
        }

    # ── lifecycle ────────────────────────────────────────────────────────────

    def open(self) -> None:
        """Open the serial port, or print available ports and exit."""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            log.info("Connected to %s at %d baud", self.port, self.baud)
        except serial.SerialException as exc:
            log.error("Could not open %s: %s", self.port, exc)
            self._print_available_ports()
            sys.exit(1)

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()
            log.info("Serial connection closed.")

    # ── reading ──────────────────────────────────────────────────────────────

    def read(self) -> None:
        """Drain every complete line currently in the serial buffer."""
        if not self.ser or not self.ser.in_waiting:
            return

        try:
            # Read all waiting bytes at once, then split into lines.
            raw = self.ser.read(self.ser.in_waiting)
            lines = raw.decode("utf-8", errors="replace").splitlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                key, value = parse_sensor_data(line)
                if key and value is not None:
                    self.data[key].append(value)
                    log.debug("%s = %s", key, value)

        except serial.SerialException as exc:
            log.warning("Serial read error: %s", exc)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _print_available_ports() -> None:
        ports = serial.tools.list_ports.comports()
        if ports:
            log.info("Available ports: %s", [p.device for p in ports])
        else:
            log.info("No serial ports detected.")


# ─── Plotting ───────────────────────────────────────────────────────────────


def _normalize(seq: deque) -> list[float]:
    """Min-max normalise a deque to [0, 1]. Safe when all values are equal."""
    lo, hi = min(seq), max(seq)
    span = hi - lo or 1.0          # avoid division by zero
    return [(v - lo) / span for v in seq]


class LivePlotter:
    """Owns the matplotlib figure and updates it every frame."""

    def __init__(self, reader: SerialReader):
        self.reader = reader

        self.fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        self.ax1, self.ax2, self.ax3, self.ax4 = axes.flat
        self.fig.suptitle("CANSAT Sensor Data Monitoring", fontsize=14, fontweight="bold")

    # ── animation callback ───────────────────────────────────────────────────

    def update(self, _frame: int) -> None:
        """Called by FuncAnimation every tick. Reads serial then redraws."""
        self.reader.read()
        d = self.reader.data

        axes = [self.ax1, self.ax2, self.ax3, self.ax4]
        for ax in axes:
            ax.clear()

        x = list(range(max((len(d[k]) for k in SENSOR_KEYS), default=0)))

        # ── Pressure ─────────────────────────────────────────────────────────
        self._plot_single(
            self.ax1, x, d["pressure"],
            color="b", marker="o",
            ylabel="Pressure (Pa)", title="Pressure",
        )

        # ── Altitude (raw vs filtered) ───────────────────────────────────────
        if d["raw_altitude"] and d["filtered_altitude"]:
            n = min(len(d["raw_altitude"]), len(d["filtered_altitude"]))
            xs = list(range(n))
            self.ax2.plot(xs, list(d["raw_altitude"])[:n],  "r-", label="Raw",      marker="o", alpha=0.7)
            self.ax2.plot(xs, list(d["filtered_altitude"])[:n], "g-", label="Filtered", marker="s", alpha=0.7)
            self._style(self.ax2, ylabel="Altitude (m)", title="Altitude", legend=True)

        # ── MPU Temperature ──────────────────────────────────────────────────
        self._plot_single(
            self.ax3, x, d["mpu_temp"],
            color="orange", marker="D",
            ylabel="Temperature (°C)", title="MPU Temperature",
        )

        # ── Normalised overlay ───────────────────────────────────────────────
        if d["pressure"] and d["filtered_altitude"] and d["mpu_temp"]:
            n = min(len(d["pressure"]), len(d["filtered_altitude"]), len(d["mpu_temp"]))
            xs = list(range(n))
            self.ax4.plot(xs, _normalize(d["pressure"])[:n],         "b-",     label="Pressure",  marker="o", alpha=0.7)
            self.ax4.plot(xs, _normalize(d["filtered_altitude"])[:n], "g-",     label="Altitude",  marker="s", alpha=0.7)
            self.ax4.plot(xs, _normalize(d["mpu_temp"])[:n],          color="orange", label="Temp", marker="D", alpha=0.7)
            self._style(self.ax4, ylabel="Normalised Value", title="All Sensors (Normalised)", legend=True)

        # ── shared x-label ───────────────────────────────────────────────────
        for ax in axes:
            ax.set_xlabel("Sample Number", fontsize=10)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _plot_single(ax, x, seq, *, color, marker, ylabel, title):
        """Plot a single deque if it has data, then style the axes."""
        if seq:
            ax.plot(x[: len(seq)], list(seq), color=color, linewidth=2, marker=marker)
        LivePlotter._style(ax, ylabel=ylabel, title=title)

    @staticmethod
    def _style(ax, *, ylabel: str, title: str, legend: bool = False):
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(f"{title} over Time", fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.3)
        if legend:
            ax.legend(loc="best")

    # ── run ──────────────────────────────────────────────────────────────────

    def start(self) -> None:
        # Keep a reference so the animation isn't garbage-collected.
        self._ani = FuncAnimation(self.fig, self.update, interval=PLOT_INTERVAL_MS)
        plt.tight_layout()
        plt.show()


# ─── Entry point ────────────────────────────────────────────────────────────


def main() -> None:
    reader = SerialReader(ARDUINO_PORT, BAUD_RATE, MAX_POINTS)
    reader.open()

    try:
        plotter = LivePlotter(reader)
        plotter.start()          # blocks until the window is closed
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
    finally:
        reader.close()


if __name__ == "__main__":
    main()