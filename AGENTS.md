# Your Own AI Analyst

A data analyst that runs inside Claude Code on the user's own CSV data. The user brings the data; this repo brings the method.

## First thing
- If `knowledge/context.md` does not exist, nothing is set up yet. Run `/setup` before anything else.
- A business question: `/analyst <question>` runs the whole chain.
- A script, notebook or run folder to check: `/validate`. Finished results to write up: `/deliver`.
- Each step (`/setup`, `/frame`, `/profile`, `/analyse`) also works alone. Skills share nothing except the files named below.

## Where things live
```
data/                    the user's CSV files; never modified
knowledge/context.md     what the data is, and `today:` (the date the data ends)
knowledge/tables/        one note per table
knowledge/quirks.md      facts about the data a human confirmed
knowledge/corrections.md dated one-line corrections from the user
helpers/                 audit, profile, checks, charts, context; the arithmetic runs here
outputs/<date>_<slug>/   one folder per question: frame.md, analysis.py, data/, charts/, review.md, brief.md
.claude/skills/          setup, analyst, frame, profile, analyse, validate, deliver
.claude/settings.json    permission rules and sandbox (enforced, unlike this file)
```
The file names above are the contract between skills. Do not rename them.

## Conventions
- Run Python with `poetry run python ...` from the repo root.
- "Today" is the `today:` line in `knowledge/context.md`, never the computer's date. Use `helpers.context.analysis_today()`.
- Never print raw rows into the conversation; aggregates only.
- Never modify anything in `data/`.
- Read `knowledge/` before touching data. When the user corrects you, append one dated line to `knowledge/corrections.md` and continue.
- Only the user confirms a quirk. Never write one into `knowledge/quirks.md` on your own.
- Mark every guess "(inferred)" until a person confirms it.
- No em dashes in anything written for a reader.

## Advice versus enforcement
This file is advice: the model follows it, but nothing forces it. `.claude/settings.json` is enforced by Claude Code for what its rules cover. Rules that matter (not editing `data/`, no deleting files) live there too. If a task seems to need one of them relaxed, ask the user; do not work around it.
