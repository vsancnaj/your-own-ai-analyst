# ✧ Your Own AI Analyst

![How it works: your CSV data goes into setup, you ask a question, five steps run, and you get a checked brief with charts](docs/workflow.svg)

**Drop in your data, ask a business question in plain words, and get a checked brief with charts. It runs inside Claude Code on your own computer.**

You bring CSV files (from Kaggle, from work, from any export). It asks a few easy questions, checks your files for problems, and then answers questions like *"what happened to sales after we changed the price?"*. Every number comes from code you can rerun, every result is compared with something, and the brief ends with a list of what was **not** verified. This tool never uploads or edits your files. Claude does read them to work, so what it reads is sent to Anthropic like any Claude Code chat; check your company's rules before using work data.

> **Not a chatbot.** The steps, the file names and the checks are fixed, so the same question gives the same kind of answer each time.

---

## Start (about 15 minutes)

> **Using Claude or another AI assistant?** Point it at this repo and say
> *"set up my analyst"*. The [AGENTS.md](AGENTS.md) file tells it what to do.

You need a computer with a terminal, [Claude Code](https://claude.com/claude-code) (with a login), [git](https://git-scm.com), Python 3.10 or 3.11 (3.12 and newer do not work yet), and [Poetry](https://python-poetry.org). If any of those words are new, ask Claude to help you install them first.

1. **Get the repo.** `git clone https://github.com/vsancnaj/your-own-ai-analyst.git` then `cd your-own-ai-analyst`
2. **Install.** `poetry install`
3. **Open Claude Code here.** Type `claude`
4. **Type `/setup`.** Answer the easy questions, copy your files into `data/` when it asks, and let it check them. **Only `.csv` files work**; export Excel or other files to CSV first.
5. **Ask.** `/analyst <your question>`

Each answer lands in its own folder under `outputs/`. Open `brief.md` (a plain text file; any text editor or your browser will show it): that is the answer, with the charts next to it.

**What it needs from you:** the CSV files, a rough idea of what the data is, and what you will do with the answer (for example "keep or undo the price change"). If you do not know something, pick "I don't know". It will measure what it can and mark the rest as a guess.

**What it will not do:** invent a question, edit your data, or present a guess as a fact.

---

# For agents (Claude Code and others)

Everything below is for the AI reading this repo. A human can stop here.

## How to behave
1. If `knowledge/context.md` is missing, run `/setup`. Nothing else works without it.
2. Read [AGENTS.md](AGENTS.md) first: layout, conventions, and the file-name contract.
3. Business question: `/analyst <question>`. The chain is frame, profile (tables without notes), analyse, validate, deliver.
4. Never answer a table question from column names alone, never print raw rows, never edit `data/`.

## The chain and its files
| Skill | Reads | Writes |
|---|---|---|
| `setup` | user answers, `data/` | `knowledge/context.md`, `quirks.md`, `corrections.md`, `tables/` |
| `frame` | question, `knowledge/` | `outputs/<run>/frame.md` |
| `profile` | one CSV, `quirks.md` | `knowledge/tables/<table>.md` |
| `analyse` | `frame.md`, `knowledge/`, `data/` | `analysis.py`, `data/`, `charts/` in the run folder |
| `validate` | the run folder | `review.md` (Ship it, Think on it, Fix first) |
| `deliver` | `review.md` first, then the run folder | `brief.md` |

File names are the only contract between skills. The model decides what to compute; code in `helpers/` computes it.

## Advice versus enforcement
| Rule | Enforced by | Note |
|---|---|---|
| Never edit `data/` | `Edit(/data/**)` deny rule, sandbox write block on `data/` | Run `/check-safety` to test it on your machine. |
| No deleting files (the usual commands) | deny rules on `rm`, `rmdir`, `git clean` | Bash rules match the usual command text only. `find -delete`, `mv` or a Python script can still delete; only the sandbox is meant to stop that, and it has to be tested. |
| Skills that must not edit | `disallowed-tools: Edit` in `frame`, `validate`, `deliver`; `/analyst` runs `validate` and `deliver` in fresh subagents | `Write` is still needed for their output files, so a skill could still overwrite a file. This limit holds only when the skill is run as its own command or subagent, not when it is read inline. |
| Aggregates only, no raw rows | a line in `AGENTS.md` and a checklist item in `validate` | Cannot be enforced by a rule. |
| Quirks only from a human | `AskUserQuestion` in `setup` and `profile` | Cannot be enforced by a rule. |

Lines explain and rules enforce. Where a rule cannot enforce something, this table says so.

## Works with
Built for Claude Code. Other agents that read `AGENTS.md` can follow the method, but `/setup`, the skills and the permission rules are Claude Code features.

## Known limits
- Reads CSV only. Date columns are found from their values; Unix-timestamp numbers are not detected.
- Quirks and "today" are only as good as the user's answers; both are marked confirmed or inferred.
- Tested only on a made-up dataset so far, not on a real user's data.
- The sandbox and the path rules in `.claude/settings.json` have not been verified on a live Claude Code session; verify them once (see the test in the setup summary) before relying on them.
- Semicolon-separated or non-UTF-8 CSVs may fail to read; the audit reports it when it notices.
