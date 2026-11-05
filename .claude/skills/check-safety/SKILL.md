---
name: check-safety
description: Tests this repo's protections by trying two harmless forbidden actions and reporting what the system did. Use after /setup, after changing .claude/settings.json, or when unsure whether the sandbox is on. Run it only when the user asks.
user-invocable: true
disable-model-invocation: true
allowed-tools: Read Bash
argument-hint: "[nothing needed]"
---

You test the protections, not the data. The user ran this skill on purpose, which is the permission for the two probes below. Do nothing else forbidden.

The failure you exist to prevent: believing `data/` is protected because a file says so, when nothing was ever tested. A rule you have not seen block something is a hope.

## Steps

1. Say in two lines what you are about to do: try one command a rule should block, and one write a sandbox should block, both on a made-up probe file in `data/`. Blocked is the good result.
2. **Probe A, the rule.** Run `rm data/.write_probe_rule`. The file does not exist, so nothing can be lost. If the system denies it ("permission denied" or similar), the rule held. If it runs and says "No such file", the rule did not block it.
3. **Probe B, the sandbox.** Run `poetry run python -c "open('data/.write_probe', 'w').write('probe')"`. If it fails with a permission or "operation not permitted" error, the sandbox held. If it succeeds, the sandbox did not protect `data/`.
4. Report one table: probe, result (held / failed), and the exact error text the system gave.
5. If Probe B succeeded, a file `data/.write_probe` now exists. Say so, and tell the user to remove it with `! rm data/.write_probe`, and to type `/sandbox` to turn the sandbox on. Do not delete it yourself.
6. Stop. Do not retry a blocked probe another way, do not edit `.claude/settings.json`, and do not touch any other file.

## What this is NOT

- Not a fix. Report what held and what did not; the user decides what to change.
- Not permission for anything beyond the two probes above.
