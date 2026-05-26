Synthesize a standup report from the local commit log.

Usage: /standup [time window]

The argument $ARGUMENTS is an optional time window (e.g. "today", "yesterday", "last 3 days", "this week"). If empty, default to the last 24 hours.

This is a purely local, read-only operation — it reads `~/.a2a/commits.jsonl` off disk. No hub or connection is involved.

## Steps

1. **Read the commit log** at `~/.a2a/commits.jsonl`. Each line is one JSON commit record with fields: `agent`, `timestamp`, `seq`, `session_id`, `cwd`, `branch`, `message`, `summary`, `files_changed`.
   - If the file does not exist or is empty, tell the user there are no commits yet and stop.

2. **Filter by the time window.** Parse `$ARGUMENTS` into a start time (default: 24 hours ago). Keep only commits whose `timestamp` falls within the window. Compute the current time with `date` if you need a reference point.

3. **Synthesize a report.** Group the commits sensibly — primarily by `agent` / project (the `agent` field defaults to the project directory name), and by `branch` where it helps. For each group, summarize the work using the `message` and `summary` fields. Collapse related commits into coherent themes rather than listing every line verbatim.

4. **Format the output** as a readable standup:
   - A short header with the time window covered and the projects/agents involved.
   - One section per project/agent, with bullet points of what was accomplished.
   - Where relevant, note the branch so the reader knows the context.

5. **Offer to drill in.** If the user wants the full history behind any commit, they can resume that session with `claude --resume <session_id>` (the `session_id` is in each commit record) or read its conversation log at `~/.claude/projects/<project>/<session_id>.jsonl`.

## Notes
- This skill only reads local files — nothing needs to be running.
- The commit log aggregates work across every session and project on this machine, so a single standup can span multiple repos.
