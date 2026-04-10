.PHONY: install hub test uninstall

VENV := .venv/bin

install:
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -e ".[dev]"
	@echo '{"mcpServers":{"a2a":{"command":"$(CURDIR)/.venv/bin/python","args":["$(CURDIR)/src/a2a/mcp_client/server.py"]}}}' > .mcp.json
	@echo "Created .mcp.json (restart Claude Code to pick up MCP tools)"

hub:
	$(VENV)/python -m a2a.hub.daemon

test:
	$(VENV)/python -m pytest tests/ -v

uninstall:
	@echo "TODO: remove MCP client entry from ~/.claude.json"
