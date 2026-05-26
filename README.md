# a2a — a local work log for Claude Code

Two slash commands that record what you do across Claude Code sessions and play it back as a standup report. Pure local files — no server, no network, nothing to run.

## Install

```bash
git clone <repo> && cd a2a
make install
```

`make install` copies `/commit` and `/standup` into `~/.claude/commands/`, so they're available in **every** project on this machine. Run it once per computer.

## Use

Record a unit of work from any session (the message is optional — a summary is generated either way):

```
> /commit fixed the rate limiter
Committed (scraper #1): Added exponential backoff on 429s.
```

Then, from anywhere, play back what you did:

```
> /standup                # last 24h
> /standup yesterday      # or: last 3 days, this week, ...
```

`/standup` reads the log and prints a report grouped by project.

## How it works

Everything lives under `~/.a2a/`, created automatically on first commit:

- **`~/.a2a/commits.jsonl`** — the append-only log. One JSON line per commit: agent, timestamp, seq, session id, cwd, branch, message, summary, files changed.
- **`~/.a2a/state/<session_id>.json`** — per-session state: the agent's name and its cursor (`seq` + `last_timestamp`). Each Claude Code session is its own "agent," auto-named after its project directory.

Design properties:

- **Per-session cursors.** `/commit` only summarizes work since your last commit *in that session*. Two sessions on one machine never clobber each other's state.
- **Atomic appends.** Each commit is a single `>>` write (`O_APPEND`), so simultaneous commits from different sessions can't interleave.
- **Drill-down.** Every commit carries its `session_id`, so you can `claude --resume <session_id>` to reopen the full conversation behind any entry.

## Uninstall

```bash
make uninstall            # removes the two skills from ~/.claude/commands/
rm -rf ~/.a2a             # optional: also delete the log
```
