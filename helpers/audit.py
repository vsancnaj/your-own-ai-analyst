"""Audit a folder of CSVs: what is in it, what looks odd, what 'today' probably is.

Used by the setup skill before any analysis. Read-only: it never writes to the data
folder, and it returns counts and names only, never raw rows.
"""

import json
import sys
from pathlib import Path

import pandas as pd

from helpers.profile import find_id_column, read_table

# A table with fewer rows than this is flagged as tiny.
TINY_TABLE_ROWS = 30
# A column with this share of missing values or more is flagged.
HIGH_NULL_RATE = 0.30
# The last month counts as partial when the data stops before this share of it.
PARTIAL_MONTH_SHARE = 0.9


# A month counts as unusual when its rows are this many times the typical month, or less.
SPIKE_FACTOR = 2.0
DIP_FACTOR = 0.5
# Tables with fewer dated rows than this are not checked for unusual months.
MIN_ROWS_FOR_MONTHS = 200
MAX_MONTH_FLAGS = 3
# The latest date column is "far ahead" when it is this many days past the next one.
COLUMNS_DISAGREE_DAYS = 31


def unusual_months(df: pd.DataFrame, col: str) -> list[dict]:
    """Return flags for months whose row count is far from the typical month.

    The first and last month are skipped because they are often partial. A flag is a
    measurement: it says the month is unusual, not why.
    """
    dates = df[col].dropna()
    if len(dates) < MIN_ROWS_FOR_MONTHS:
        return []
    counts = dates.dt.to_period("M").value_counts().sort_index()
    if len(counts) < 5:
        return []
    inner = counts.iloc[1:-1]
    typical = float(inner.median())
    if typical == 0:
        return []
    odd = inner[(inner > SPIKE_FACTOR * typical) | (inner < DIP_FACTOR * typical)]
    odd = odd.reindex((odd / typical - 1).abs().sort_values(ascending=False).index)
    return [
        {
            "what": (f"{month} has {int(n):,} rows in `{col}`, about {n / typical:.1f} times "
                     f"a typical month ({typical:,.0f})."),
            "affects": "any comparison that includes that month; ask whether something happened then",
        }
        for month, n in odd.head(MAX_MONTH_FLAGS).items()
    ]


def date_order_flags(df: pd.DataFrame) -> list[dict]:
    """Return flags for date columns whose day and month order could not be told."""
    messages = {
        "ambiguous": "could be day-first or month-first (every value fits both); read as month-first unless told otherwise",
        "mixed": "has values in both day-first and month-first order",
    }
    return [
        {
            "what": f"`{col}` {messages[order]}.",
            "affects": "every date in that column: days can land in the wrong month, and so can 'today'",
        }
        for col, order in df.attrs.get("date_notes", {}).items()
    ]


def audit_table(path: Path) -> dict:
    """Return the facts and the flags for one CSV file.

    Each flag is a dict with `what` (the plain-words finding) and `affects` (what it
    would damage if ignored). A flag is a measurement, not a verdict.
    """
    flags = []
    try:
        df = read_table(path)
    except Exception as error:  # noqa: BLE001 - any read failure is itself the finding
        return {
            "table": path.stem,
            "file": path.name,
            "readable": False,
            "flags": [{
                "what": f"The file could not be read ({type(error).__name__}).",
                "affects": "everything: this table cannot be used until it opens",
            }],
        }

    if df.shape[1] == 1 and any(sep in str(df.columns[0]) for sep in (";", "\t", "|")):
        flags.append({
            "what": "The whole file was read as one column, so it probably uses a different separator.",
            "affects": "everything: no column below is real until the file is exported with commas",
        })

    if len(df) == 0:
        flags.append({"what": "The table has no rows.", "affects": "every question that needs it"})
    elif len(df) < TINY_TABLE_ROWS:
        flags.append({
            "what": f"Only {len(df)} rows.",
            "affects": "rates and charts: small counts swing a lot",
        })

    id_column = find_id_column(df)
    duplicate_ids = int(df[id_column].duplicated().sum()) if id_column else None
    if duplicate_ids:
        flags.append({
            "what": f"`{id_column}` repeats {duplicate_ids:,} times, so it is not one row per id.",
            "affects": "any count and any join on this table (rows can multiply)",
        })

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        flags.append({
            "what": f"{duplicate_rows:,} rows are exact copies of another row.",
            "affects": "every count and sum: they are counted twice",
        })
        if id_column:
            repeats_after = int(df.drop_duplicates()[id_column].duplicated().sum())
            if repeats_after:
                flags.append({
                    "what": (f"Even after removing exact copies, `{id_column}` still repeats "
                             f"{repeats_after:,} times: the same id with different content."),
                    "affects": "any count by id and any join; ask which version is right",
                })

    columns = []
    for col in df.columns:
        null_rate = float(df[col].isna().mean())
        columns.append({"name": col, "dtype": str(df[col].dtype), "null_rate": round(null_rate, 4)})
        if null_rate >= HIGH_NULL_RATE:
            flags.append({
                "what": f"`{col}` is empty in {null_rate:.0%} of rows.",
                "affects": "any rate or filter on that column; ask what empty means",
            })

    flags += date_order_flags(df)

    date_columns = []
    for col in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            continue
        values = df[col].dropna()
        if values.empty:
            continue
        flags += unusual_months(df, col)
        date_columns.append({
            "name": col,
            "min": values.min().date().isoformat(),
            "max": values.max().date().isoformat(),
        })

    return {
        "table": path.stem,
        "file": path.name,
        "readable": True,
        "rows": len(df),
        "id_column": id_column,
        "columns": columns,
        "date_columns": date_columns,
        "flags": flags,
    }


def shared_columns(tables: list[dict]) -> list[dict]:
    """Return column names that appear in more than one table: likely join keys.

    This is a name match only. Whether the two columns mean the same thing is for the
    user to confirm.
    """
    seen: dict[str, list[str]] = {}
    for table in tables:
        if not table["readable"]:
            continue
        for col in table["columns"]:
            seen.setdefault(col["name"], []).append(table["table"])
    return [
        {"column": name, "tables": names}
        for name, names in seen.items()
        if len(names) > 1
    ]


def guess_today(tables: list[dict]) -> dict:
    """Guess 'today' as the latest date found anywhere in the data.

    Also says whether the last month looks partial, because a partial month must not be
    read as a result. The user confirms or corrects the date.
    """
    by_column = []
    for table in tables:
        for col in table.get("date_columns", []):
            by_column.append({"column": f"{table['table']}.{col['name']}", "max": col["max"]})
    if not by_column:
        return {"found": False, "note": "No date columns found, so no 'today' can be guessed."}
    by_column.sort(key=lambda c: c["max"], reverse=True)
    latest = pd.Timestamp(by_column[0]["max"])
    latest_where = by_column[0]["column"]
    # A column of renewal, due or expiry dates reaches into the future and would pull the
    # guess past the real end of the data. Say so when the columns disagree by over a month.
    columns_disagree = (
        len(by_column) > 1
        and (latest - pd.Timestamp(by_column[1]["max"])).days > COLUMNS_DISAGREE_DAYS
    )
    month_days = latest.days_in_month
    partial = (latest.day / month_days) < PARTIAL_MONTH_SHARE
    return {
        "found": True,
        "latest_date": latest.date().isoformat(),
        "found_in": latest_where,
        "last_month_looks_partial": bool(partial),
        "latest_column_is_far_ahead": bool(columns_disagree),
        "by_column": by_column,
    }


def audit_folder(data_dir: str | Path = "data") -> dict:
    """Audit every CSV in a folder and return the full picture as one dict."""
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        return {"folder": str(data_dir), "error": f"Folder {data_dir} does not exist.",
                "csv_files": [], "tables": [], "shared_columns": [], "other_files_ignored": [],
                "today_guess": {"found": False, "note": "No data folder."}}
    # Match .csv in any letter case (DATA.CSV is a CSV too).
    everything = sorted(p for p in data_dir.iterdir() if p.is_file() and p.name != ".gitkeep")
    files = [p for p in everything if p.suffix.lower() == ".csv"]
    other = [p.name for p in everything if p.suffix.lower() != ".csv"]
    tables = [audit_table(p) for p in files]
    return {
        "folder": str(data_dir),
        "csv_files": [p.name for p in files],
        "other_files_ignored": other,
        "tables": tables,
        "shared_columns": shared_columns(tables),
        "today_guess": guess_today(tables),
    }


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(json.dumps(audit_folder(folder), indent=2, default=str))
