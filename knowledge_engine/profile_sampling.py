"""Sample a measured rotational profile without wasting loops on flat spans."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def _profile_arrays(rows: Sequence[dict]) -> tuple[np.ndarray, np.ndarray]:
    if len(rows) < 4:
        raise ValueError("profile requires at least four measured rows")
    points = sorted(
        (float(row["y_norm_top_to_bottom"]), float(row["width_norm"]))
        for row in rows
    )
    positions = np.asarray([point[0] for point in points], dtype=float)
    widths = np.asarray([point[1] for point in points], dtype=float)
    if not np.isfinite(positions).all() or not np.isfinite(widths).all():
        raise ValueError("profile values must be finite")
    if positions[0] < 0.0 or positions[-1] > 1.0 or np.any(np.diff(positions) <= 0.0):
        raise ValueError("profile positions must be unique, increasing, and inside [0, 1]")
    if np.any(widths < 0.0):
        raise ValueError("profile widths cannot be negative")
    return positions, widths


def smooth_profile_widths(rows: Sequence[dict], window: int = 21) -> tuple[np.ndarray, np.ndarray]:
    """Return edge-preserving moving-average widths for noisy silhouette rows."""
    positions, widths = _profile_arrays(rows)
    if window < 1:
        raise ValueError("window must be positive")
    window = min(int(window), len(widths) if len(widths) % 2 else len(widths) - 1)
    window = max(1, window | 1)
    radius = window // 2
    padded = np.pad(widths, (radius, radius), mode="edge")
    smoothed = np.convolve(padded, np.ones(window, dtype=float) / window, mode="valid")
    return positions, smoothed


def adaptive_profile_positions(
    rows: Sequence[dict],
    count: int,
    *,
    smoothing_window: int = 21,
    curvature_bias: float = 6.0,
    slope_bias: float = 1.5,
) -> list[float]:
    """Distribute rings toward measured bends while retaining broad coverage.

    Positions are normalized from image top (0) to bottom (1). The method uses
    bounded slope and curvature signals, so segmentation spikes cannot consume
    the whole loop budget. It chooses positions only; it does not invent width.
    """
    if not 4 <= count <= 256:
        raise ValueError("count must be between 4 and 256")
    if curvature_bias < 0.0 or slope_bias < 0.0:
        raise ValueError("sampling biases cannot be negative")
    positions, widths = smooth_profile_widths(rows, smoothing_window)
    if count > len(positions):
        raise ValueError("count cannot exceed measured profile rows")

    slope = np.gradient(widths, positions)
    curvature = np.gradient(slope, positions)

    def bounded_signal(values: np.ndarray) -> np.ndarray:
        magnitude = np.abs(values)
        scale = float(np.percentile(magnitude, 90.0))
        if scale <= 1e-12:
            return np.zeros_like(magnitude)
        return np.minimum(magnitude / scale, 2.0)

    importance = (
        1.0
        + slope_bias * bounded_signal(slope)
        + curvature_bias * bounded_signal(curvature)
    )
    interval_mass = 0.5 * (importance[:-1] + importance[1:]) * np.diff(positions)
    cumulative = np.concatenate(([0.0], np.cumsum(interval_mass)))
    targets = np.linspace(0.0, cumulative[-1], count)
    sampled = np.interp(targets, cumulative, positions)
    sampled[0], sampled[-1] = positions[0], positions[-1]
    return [float(value) for value in sampled]


def profile_width_at(
    rows: Sequence[dict], position: float, *, smoothing_window: int = 21
) -> float:
    """Interpolate a denoised measured width at one normalized position."""
    if not 0.0 <= position <= 1.0:
        raise ValueError("position must be inside [0, 1]")
    positions, widths = smooth_profile_widths(rows, smoothing_window)
    return float(np.interp(position, positions, widths))
