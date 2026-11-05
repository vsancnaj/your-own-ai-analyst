"""Profile a CSV: shape, types, nulls, ids, date ranges and small value sets."""

import json
import re
import sys
from pathlib import Path

import pandas as pd

from helpers.context import saved_date_order

# Columns with this many distinct values or fewer get their full value counts listed.
LOW_CARDINALITY_MAX = 20

# A text column counts as a date column when this share of a sample parses as dates.
DATE_PARSE_SHARE = 0.95
SAMPLE_SIZE = 500

# Dates look like 2024-03-18, 18/03/2024, 03/18/2024 or Mar 18, 2024: digits and separators,
# or a month name. Plain numbers such as 42 or 3.14 do not.
_DATE_SHAPE = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}|[A-Za-z]{3,9}\.? \d{1,2},? \d{4}")


_SLASH_DATE = re.compile(r"^\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})")


def date_order(series: pd.Series) -> str | None:
    """Say how a text column writes dates when they use slashes, dots or dashes first.

    Returns 'day-first' (a value like 25/03/2024 can only be day first), 'month-first'
    (like 03/25/2024), 'mixed' (both appear), 'ambiguous' (every value could be either,
    like 03/04/2024) or None when the column has no such dates (for example 2024-03-18).
    Reading these the wrong way round puts days in the wrong months without any error.
    """
    parts = series.dropna().astype(str).str.extract(_SLASH_DATE).dropna()
    if parts.empty:
        return None
    first_over_12 = int(parts[0].astype(int).max()) > 12
    second_over_12 = int(parts[1].astype(int).max()) > 12
    if first_over_12 and second_over_12:
        return "mixed"
    if first_over_12:
        return "day-first"
    if second_over_12:
        return "month-first"
    return "ambiguous"


def looks_like_dates(series: pd.Series) -> bool:
    """Return True if a text column mostly holds values shaped like dates.

    Looks at a sample only, so it stays fast on large tables.
    """
    sample = series.dropna().astype(str).head(SAMPLE_SIZE)
    if sample.empty:
        return False
    shaped = sample.map(lambda v: bool(_DATE_SHAPE.search(v)))
    if shaped.mean() < DATE_PARSE_SHARE:
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return float(parsed.notna().mean()) >= DATE_PARSE_SHARE


def find_date_columns(df: pd.DataFrame) -> list[str]:
    """Return the columns that hold dates: already typed as dates, or text shaped like dates.

    Decided from the values, not the name: a text column needs date-shaped values, and a
    numeric column is never a date. Known limit: numbers that are Unix timestamps (for
    example 1710000000) are not detected; the audit reports them as numbers and the
    user can say which column is a date.
    """
    found = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            found.append(col)
        elif df[col].dtype == object and looks_like_dates(df[col]):
            found.append(col)
    return found


def find_id_column(df: pd.DataFrame) -> str | None:
    """Return the column most likely to be the table's key, or None.

    Candidates are a column named `id` or ending in `_id` or `Id`. The first candidate
    whose values are all different wins (so a foreign key such as customer_id in an orders
    table is passed over for order_id). If none is unique, the first candidate is returned
    and the duplicates are reported by the caller.
    """
    candidates = [
        col for col in df.columns
        if col.lower() == "id" or col.lower().endswith("_id") or (col.endswith("Id") and len(col) > 2)
    ]
    for col in candidates:
        if df[col].is_unique:
            return col
    return candidates[0] if candidates else None


def read_table(path: str | Path) -> pd.DataFrame:
    """Read one CSV, parsing the columns that hold dates. Never writes anything.

    Day-first or month-first is worked out from the values. When the values cannot say
    ('ambiguous' or 'mixed'), the order the user gave the setup is used, else
    month-first. What was found is left in `df.attrs["date_notes"]` as
    {column: order} so the audit can report it.
    """
    df = pd.read_csv(path, low_memory=False)
    notes = {}
    fallback = saved_date_order()
    for col in find_date_columns(df):
        if df[col].dtype == object:
            order = date_order(df[col])
            if order in ("ambiguous", "mixed"):
                notes[col] = order
            dayfirst = order == "day-first" or (order in ("ambiguous", "mixed") and fallback == "day-first")
        else:
            dayfirst = False
        df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed", dayfirst=dayfirst)
    df.attrs["date_notes"] = notes
    return df


def profile_csv(path: str | Path) -> dict:
    """Return a profile of one CSV: shape, types, nulls, ids, date ranges and small value sets.

    Use it when meeting a table for the first time, before any analysis.
    """
    path = Path(path)
    df = read_table(path)
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    columns = [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_rate": round(float(df[col].isna().mean()), 4),
            "distinct": int(df[col].nunique()),
        }
        for col in df.columns
    ]

    # The first id-like column is taken as the table's key; duplicates there mean the
    # table is not one row per id.
    id_column = find_id_column(df)
    duplicate_ids = int(df[id_column].duplicated().sum()) if id_column else 0

    date_columns = []
    for col in date_cols:
        values = df[col].dropna()
        date_columns.append({
            "name": col,
            "min": values.min().isoformat() if len(values) else None,
            "max": values.max().isoformat() if len(values) else None,
        })

    low_cardinality = {}
    for col in df.columns:
        if col in date_cols or df[col].nunique() > LOW_CARDINALITY_MAX:
            continue
        # value_counts leaves nulls out; the null rate is already in the columns table.
        counts = df[col].value_counts()
        low_cardinality[col] = {str(k): int(v) for k, v in counts.items()}

    if id_column is None:
        grain_guess = None
    elif duplicate_ids == 0:
        grain_guess = f"one row per {id_column}"
    else:
        grain_guess = f"not one row per {id_column}; check the grain"

    return {
        "table": path.stem,
        "rows": len(df),
        "columns": columns,
        "id_column": id_column,
        "duplicate_ids": duplicate_ids,
        "date_columns": date_columns,
        "low_cardinality": low_cardinality,
        "grain_guess": grain_guess,
        "date_notes": df.attrs.get("date_notes", {}),
    }


def profile_to_markdown(result: dict) -> str:
    """Return a profile from profile_csv as a markdown note, ready for knowledge/tables/."""
    grain = result["grain_guess"] or "no id column found"
    lines = [
        f"# {result['table']}",
        "",
        f"Grain (a guess from the data, confirm it): {grain}. "
        f"{result['rows']:,} rows.",
        "",
        "## Columns",
        "",
        "| Name | Type | Null rate | Distinct |",
        "| --- | --- | --- | --- |",
    ]
    for col in result["columns"]:
        lines.append(
            f"| {col['name']} | {col['dtype']} | {col['null_rate']:.2%} "
            f"| {col['distinct']:,} |"
        )

    lines += ["", "## Date ranges", ""]
    if result["date_columns"]:
        for col in result["date_columns"]:
            lines.append(f"- `{col['name']}`: {col['min']} to {col['max']}")
    else:
        lines.append("- None")

    for col, order in result.get("date_notes", {}).items():
        lines.append(
            f"- Warning: `{col}` has dates whose day and month order is {order}; "
            "they were read month-first unless the setup recorded otherwise. Confirm."
        )

    lines += ["", "## Low-cardinality values", ""]
    if result["low_cardinality"]:
        for name, counts in result["low_cardinality"].items():
            values = ", ".join(f"{k} ({v:,})" for k, v in counts.items())
            lines.append(f"- `{name}`: {values}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Meaning",
        "",
        "Fill in what each column means for the business.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python helpers/profile.py <path-to-csv>")
    print(json.dumps(profile_csv(sys.argv[1]), indent=2, default=str))
