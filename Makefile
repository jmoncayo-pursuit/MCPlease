SHELL := /bin/bash

.PHONY: clean-mcp prune-mcp

clean-mcp:
	python3 scripts/clean_mcp_contexts.py --all

prune-mcp:
	python3 scripts/clean_mcp_contexts.py --days 7


