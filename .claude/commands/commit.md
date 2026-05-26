Record a unit of work to the local shared commit log.

Usage: /commit [message]

The argument $ARGUMENTS is an optional human-readable message describing the work (like a git commit message). If it is empty, that is fine — the generated `summary` carries the record on its own.

This is a purely local operation — it writes files under `~/.a2a/`. No hub, no network, no connection required.

## Steps

1. **Find this session's id.** Run:
   ```
   ls -t ~/.claude/projects/$(pwd | sed 's#/#-#g')/*.jsonl 2>/dev/null | head -1 | xargs -r basename | sed 's/\.jsonl$//'
   ```
   Call the result `SESSION_ID`. If it comes back empty, use the literal string `default` as `SESSION_ID` and omit `session_id` from the commit record in step 5.

2. **Read this session's state** from `~/.a2a/state/<SESSION_ID>.json` if it exists. It looks like `{"name": "a2a", "seq": 2, "last_timestamp": "2026-05-25T14:15:00Z"}`.
   - If it exists: take `name` and `last_timestamp` from it; the new sequence number is `seq + 1`; summarize work done **since** `last_timestamp`.
   - If it does not exist (first commit this session): the new sequence number is `1`; summarize the **entire** conversation so far; the `name` defaults to the basename of the current directory (`basename "$(pwd)"`).

3. **Generate the summary.** From your conversation context in that window, write:
   - `summary`: 1-3 sentences on what was actually accomplished (outcomes, not a play-by-play).
   - `files_changed`: list of file paths you created or modified in that window (from your memory of the conversation). Empty list if none.

4. **Gather metadata** by running:
   - `cwd`: `pwd`
   - `branch`: `git rev-parse --abbrev-ref HEAD 2>/dev/null` (leave empty / null if not in a git repo)
   - `timestamp`: `date -u +%Y-%m-%dT%H:%M:%SZ`

5. **Append the commit.** Build this JSON object on a single line and append it to `~/.a2a/commits.jsonl` (create `~/.a2a/` first with `mkdir -p ~/.a2a`):
   ```json
   {"agent": "<name>", "timestamp": "<timestamp>", "seq": <new_seq>, "session_id": "<SESSION_ID>", "cwd": "<cwd>", "branch": "<branch>", "message": "$ARGUMENTS", "summary": "<summary>", "files_changed": [...]}
   ```
   If no message was given, set `"message"` to an empty string `""`. Append it with a single `>>` redirect (one atomic write) so concurrent commits from other sessions can't interleave. Do **not** rewrite the whole file — only append.

6. **Update this session's state.** Write `~/.a2a/state/<SESSION_ID>.json` (create `~/.a2a/state/` if needed) with the new `name`, `seq`, and `last_timestamp` (= this commit's `timestamp`). This is what makes the next `/commit` incremental and per-session.

7. **Confirm** to the user: the agent name, the sequence number, and a one-line recap of what was committed.

## Notes
- The `message` is the user's optional annotation (the "why"); the `summary` is your generated detail (the "what"). Both are stored. When no message is given, the summary stands alone.
- This is not a git commit — the user does not need to have run `git commit`. The summary comes from the conversation, not from git.
- Each Claude Code session is its own "agent" with its own cursor, keyed by `SESSION_ID`. Two sessions on the same machine never share or clobber each other's state. The agent `name` defaults to the project directory, so commits group by project at standup time; edit `~/.a2a/state/<SESSION_ID>.json` to rename.
