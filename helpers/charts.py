"""Chart helpers with one house style.

Three rules:
1. Gray first, color for focus: everything is gray except what the reader should look at.
2. The title is the takeaway: pass the sentence the chart proves, not a label.
3. Label directly: values sit on the bars and names at the end of lines, no legend.
"""

from collections.abc import Sequence
from pathlib import Path

import matplotlib

# Agg draws to files, not a window. Scripts run from the terminal with no
# display, so this must be set before pyplot is imported.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

# Gray for context, one accent color for the thing the reader should see.
GRAY = "#B0B0B0"
ACCENT = "#1F6FEB"
TEXT = "#333333"


def _as_list(highlight) -> list:
    if highlight is None:
        return []
    if isinstance(highlight, (list, tuple, set)):
        return list(highlight)
    return [highlight]


def _style(ax, title: str, ylabel: str | None, source: str | None) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(False)
    ax.tick_params(colors=TEXT)
    ax.set_title(title, loc="left", fontweight="bold", color=TEXT)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT)
    if source:
        ax.figure.text(0.01, 0.01, source, fontsize=8, color=GRAY, ha="left")


def bar(
    categories, values, title, highlight=None, ylabel=None, source=None,
    horizontal=False, value_fmt="{:,.0f}",
) -> Figure:
    """Return a bar chart with the `highlight` categories in color and the rest gray.

    Use it to compare a value across groups; set horizontal=True for long names.
    value_fmt formats the number on each bar. The default shows whole numbers;
    pass "{:.1f}" for rates and percentages, or 12.4 will be shown as 12.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    focus = _as_list(highlight)
    colors = [ACCENT if c in focus else GRAY for c in categories]
    labels = [str(c) for c in categories]
    if horizontal:
        bars = ax.barh(labels, values, color=colors)
        # barh draws the first category at the bottom; flip so it reads top-down.
        ax.invert_yaxis()
    else:
        bars = ax.bar(labels, values, color=colors)
    # Values sit on the bars, so the reader does not have to read an axis.
    ax.bar_label(bars, fmt=value_fmt, padding=3, color=TEXT)
    _style(ax, title, ylabel, source)
    fig.tight_layout()
    return fig


def line(
    x, series: dict[str, Sequence], title, highlight=None, ylabel=None, source=None
) -> Figure:
    """Return a line chart with one line per entry in `series`, named at its end.

    Use it for trends over time; pass the lines to color in `highlight`.
    """
    fig, ax = plt.subplots(figsize=(9, 5))
    focus = _as_list(highlight)
    x = list(x)
    for name, ys in series.items():
        ys = list(ys)
        color = ACCENT if name in focus else GRAY
        ax.plot(x, ys, color=color, linewidth=2 if name in focus else 1.5)
        # Name each line at its last point instead of using a legend.
        ax.annotate(
            name, xy=(x[-1], ys[-1]), xytext=(5, 0), textcoords="offset points",
            va="center", color=color, fontweight="bold" if name in focus else None,
        )
    # Month names side by side overlap on a wide time axis; tilt them so each stays readable.
    ax.tick_params(axis="x", rotation=45)
    _style(ax, title, ylabel, source)
    fig.tight_layout()
    return fig


def save(fig: Figure, path: str | Path) -> Path:
    """Save the chart as a PNG at `path`, creating folders as needed, and return the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    # Close the figure so a script that makes many charts does not hold them all in memory.
    plt.close(fig)
    return path
