.PHONY: install hub test uninstall

VENV := .venv/bin

install:
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -e ".[dev]"

hub:
	$(VENV)/python -m a2a.hub.daemon

test:
	$(VENV)/python -m pytest tests/ -v

uninstall:
	@echo "TODO: remove MCP client entry from ~/.claude.json"
