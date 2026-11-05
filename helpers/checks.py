"""Sanity checks for analysis results. Each returns ok, a summary and its numbers."""

from collections.abc import Iterable

import pandas as pd

from helpers.context import analysis_today


def parts_sum_to_total(
    parts: Iterable[float], total: float, tolerance: float = 0.005
) -> dict:
    """Check that segment values add back to the overall total, within a tolerance.

    Use it after splitting a number by segment, to catch rows lost or counted twice.
    """
    parts_sum = float(sum(parts))
    # Compare as a relative difference so the tolerance works for counts and revenue alike.
    rel_diff = abs(parts_sum - total) / abs(total) if total else abs(parts_sum)
    ok = rel_diff <= tolerance
    verdict = "match" if ok else "do not match"
    return {
        "ok": ok,
        "summary": (
            f"The parts sum to {parts_sum:,.2f} against a total of {total:,.2f} "
            f"({rel_diff:.2%} apart), so they {verdict}."
        ),
        "parts_sum": parts_sum,
        "total": total,
        "relative_difference": rel_diff,
        "tolerance": tolerance,
    }


def join_fan_out(
    left: pd.DataFrame, right: pd.DataFrame, on: str | list[str]
) -> dict:
    """Check whether joining `right` onto `left` multiplies rows.

    Use it before trusting any join; a fan-out silently inflates sums and counts.
    """
    rows_before = len(left)
    # A left join never drops rows, so any change in the row count is a fan-out. An inner
    # join would hide it whenever unmatched keys remove as many rows as duplicates add.
    merged = left.merge(right, on=on, how="left", indicator="_join_side")
    rows_after = len(merged)
    unmatched = int((merged["_join_side"] == "left_only").sum())
    duplicate_keys = int(right.duplicated(subset=on).sum())
    ok = rows_after == rows_before
    if ok:
        summary = f"The join kept all {rows_before:,} rows without fanning out."
        if unmatched:
            summary += (f" {unmatched:,} rows have no match in the right table, so an inner "
                        "join would drop them.")
    else:
        summary = (
            f"The join grew {rows_before:,} rows to {rows_after:,} because the "
            f"right table repeats {duplicate_keys:,} keys."
        )
    return {
        "ok": ok,
        "summary": summary,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicate_keys_right": duplicate_keys,
        "unmatched_left": unmatched,
    }


def today_vs_data(df: pd.DataFrame, col: str, tolerance_days: int = 7) -> dict:
    """Check that the saved analysis date matches the last date in the data.

    A "today" far after the data's end makes unfinished periods look complete; a "today"
    before it silently drops real rows. Either flips headline numbers without any error.
    """
    latest = pd.to_datetime(df[col]).max()
    today = analysis_today()
    gap = int((today - latest.normalize()).days)
    ok = abs(gap) <= tolerance_days
    if ok:
        summary = f"Analysis date {today.date()} matches the data's last date {latest.date()}."
    else:
        where = "after" if gap > 0 else "before"
        summary = (f"Analysis date {today.date()} is {abs(gap)} days {where} the data's last date "
                   f"{latest.date()} in `{col}`. Check knowledge/context.md before trusting results.")
    return {"ok": ok, "summary": summary, "gap_days": gap, "data_last_date": latest.date().isoformat()}


def date_boundaries(df: pd.DataFrame, col: str, freq: str = "M") -> dict:
    """Check whether the first and last periods of a date column are only partly covered.

    Use it before comparing periods, so a half month is not read as a drop.
    """
    dates = pd.to_datetime(df[col]).dropna()
    # Normalise to midnight so a timestamp late on the last day still counts as
    # covering that day when compared with the period's start and end.
    min_day, max_day = dates.min().normalize(), dates.max().normalize()
    first, last = min_day.to_period(freq), max_day.to_period(freq)
    first_partial = min_day > first.start_time.normalize()
    last_partial = max_day < last.end_time.normalize()

    partial = []
    if first_partial:
        partial.append(f"the first period ({first}) starts on {min_day.date()}")
    if last_partial:
        partial.append(f"the last period ({last}) ends on {max_day.date()}")
    if partial:
        summary = f"Partial edges in {col}: " + " and ".join(partial) + "."
    else:
        summary = f"Both edge periods of {col} ({first} and {last}) are complete."

    return {
        "ok": not partial,
        "summary": summary,
        "first_period": str(first),
        "last_period": str(last),
        "first_partial": bool(first_partial),
        "last_partial": bool(last_partial),
        "min_date": min_day.date().isoformat(),
        "max_date": max_day.date().isoformat(),
    }


def matured_only(df: pd.DataFrame, end_col: str, as_of=None) -> dict:
    """Return only the rows whose window has closed by `as_of`.

    `as_of` defaults to the analysis date saved by the setup (`knowledge/context.md`),
    never the computer's calendar date.

    Use it for anything still running (a trial, an order in transit, an open month),
    whose outcome is not known yet.
    """
    as_of = pd.Timestamp(as_of) if as_of is not None else analysis_today()
    ends = pd.to_datetime(df[end_col])
    kept = df[ends <= as_of]
    dropped = len(df) - len(kept)
    no_end = int(ends.isna().sum())
    return {
        "ok": dropped == 0,
        "summary": (
            f"Excluded {dropped:,} of {len(df):,} rows as not closed by {as_of.date()}: "
            f"{dropped - no_end:,} end after that date and {no_end:,} have no end date "
            "(still open, or never ending; decide which before reading the rest)."
        ),
        "kept": kept,
        "dropped": dropped,
        "dropped_no_end_date": no_end,
        "as_of": as_of.date().isoformat(),
    }


if __name__ == "__main__":
    # Quick demo on made-up data, so it runs on any repo.
    demo = pd.DataFrame({"start": pd.date_range("2024-01-15", periods=60, freq="D")})
    result = date_boundaries(demo, "start")
    for key, value in result.items():
        print(f"{key}: {value}")
