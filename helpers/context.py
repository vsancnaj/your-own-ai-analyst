"""Read the facts the setup saved in knowledge/context.md.

The one that matters most is 'today': the date the data ends. Analyses must use it
instead of the computer's calendar, or an old export looks stale and a partial month
looks like a result.
"""

import re
from pathlib import Path

import pandas as pd

CONTEXT_PATH = Path("knowledge/context.md")
_TODAY_LINE = re.compile(r"^\s*-?\s*\**today\**\s*:\s*\**\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE | re.MULTILINE)


def analysis_today(path: str | Path = CONTEXT_PATH) -> pd.Timestamp:
    """Return the analysis date saved by the setup, as a Timestamp.

    Stops with a clear message when the setup has not been run, rather than falling
    back to the real date.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run /setup first so the analysis knows what 'today' is."
        )
    match = _TODAY_LINE.search(path.read_text())
    if not match:
        raise ValueError(f"No 'today: YYYY-MM-DD' line in {path}. Run /setup again.")
    return pd.Timestamp(match.group(1))


_ORDER_LINE = re.compile(r"^\s*-?\s*\**date_order\**\s*:\s*\**\s*(day-first|month-first)", re.IGNORECASE | re.MULTILINE)


def saved_date_order(path: str | Path = CONTEXT_PATH) -> str | None:
    """Return 'day-first' or 'month-first' if the user told the setup, else None.

    Only used when the dates themselves cannot say (for example 03/04/2024 with no
    day above 12 anywhere in the column).
    """
    path = Path(path)
    if not path.exists():
        return None
    match = _ORDER_LINE.search(path.read_text())
    return match.group(1).lower() if match else None


if __name__ == "__main__":
    print(analysis_today().date().isoformat())
