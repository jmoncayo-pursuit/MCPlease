SHELL := /bin/bash

.PHONY: clean-mcp prune-mcp docker-start docker-prod docker-dev docker-stop docker-logs test-installer

clean-mcp:
	python3 scripts/clean_mcp_contexts.py --all

prune-mcp:
	python3 scripts/clean_mcp_contexts.py --days 7

# Docker commands
docker-start:
	./start-docker.sh

docker-prod:
	./start-docker.sh prod

docker-dev:
	./start-docker.sh dev

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Testing commands
test-installer:
	python3 scripts/test_installer.py

test-installer-dry-run:
	./scripts/test_installer_dry_run.sh


