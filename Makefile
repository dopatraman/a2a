.PHONY: install uninstall

COMMANDS := $(HOME)/.claude/commands

# Install the /commit and /standup skills for use in any project on this machine.
# Pure markdown — no Python, no dependencies, nothing to run.
install:
	mkdir -p $(COMMANDS)
	cp .claude/commands/commit.md .claude/commands/standup.md $(COMMANDS)/
	@echo "Installed /commit and /standup to $(COMMANDS)"

uninstall:
	rm -f $(COMMANDS)/commit.md $(COMMANDS)/standup.md
	@echo "Removed /commit and /standup from $(COMMANDS)"
