## Public make targets
.PHONY: # Help output
.PHONY: help
.PHONY:
.PHONY: # Manage container image
.PHONY: clean build debug-build config
.PHONY:
.PHONY: # Manage MCP server for Testing Farm
.PHONY: run-mcp-testing-farm stop-mcp-testing-farm logs-mcp-testing-farm
.PHONY:
.PHONY: # Start Goose container without a specific recipe
.PHONY: run-goose run-goose-bash
.PHONY:
.PHONY: # Run Goose with specific recipes
.PHONY: test-reverse-dependencies
.PHONY:
.PHONY: # Development and testing
.PHONY: check check-find-package-dependents-script

## Defaults
COMPOSE ?= podman compose

test-reverse-dependencies: ARCH ?= x86_64
test-reverse-dependencies: PACKAGE ?= podman
test-reverse-dependencies: CHANGE ?=
test-reverse-dependencies: DIST_GIT_BRANCH ?= c10s
test-reverse-dependencies: GIT_URL ?= https://gitlab.com/redhat/centos-stream/rpms
test-reverse-dependencies: RPM_COMPOSE ?= CentOS-Stream-10

## Operations
build:
	$(COMPOSE) build

debug-build:
	BUILD_TARGET=debug $(COMPOSE) build

run-mcp-testing-farm:
	$(COMPOSE) up -d mcp-testing-farm

stop-mcp-testing-farm:
	$(COMPOSE) down mcp-testing-farm

logs-mcp-testing-farm:
	$(COMPOSE) logs -f mcp-testing-farm

run-goose:
	- $(COMPOSE) up -d goose
	$(COMPOSE) exec goose goose

run-goose-bash:
	- $(COMPOSE) up -d goose
	$(COMPOSE) exec goose bash

test-reverse-dependencies:
	$(COMPOSE) run --rm \
		--entrypoint /bin/sh goose \
		-c "/usr/local/bin/goose run --recipe recipes/test-reverse-dependencies.yaml \
			--params arch=$(ARCH) \
			--params package=$(PACKAGE) \
			--params change='$(CHANGE)' \
			--params git_url=$(GIT_URL) \
			--params dist_git_branch=$(DIST_GIT_BRANCH) \
			--params compose=$(RPM_COMPOSE)"

config: GLOBAL_TEMPLATE = templates/compose.env
config: SECRET_TEMPLATES = $(filter-out $(GLOBAL_TEMPLATE), $(wildcard templates/*))
config:
	mkdir -p .secrets
	cp -n $(SECRET_TEMPLATES) .secrets/
	cp -n $(GLOBAL_TEMPLATE) .env

clean:
	$(COMPOSE) down
	podman volume prune -f

check: check-find-package-dependents-script

check-find-package-dependents-script:
	cd scripts && python tests/test-find-package-dependents.py

help:
	@echo "Available targets:"
	@echo "  config                      - Copy config templates to .secrets/ and .env"
	@echo "  build                       - Build all images"
	@echo "  debug-build                 - Build all images and rebuild goose from source"
	@echo "  run-mcp-testing-farm        - Start testing-farm MCP server in background"
	@echo "  stop-mcp-testing-farm       - Stop testing-farm MCP server"
	@echo "  logs-mcp-testing-farm       - Show testing-farm MCP server logs"
	@echo "  run-goose                   - Run goose interactively"
	@echo "  run-goose-bash              - Run goose with bash shell"
	@echo "  test-reverse-dependencies   - Test all reverse dependencies of a package"
	@echo "  check                       - Run all development tests"
	@echo "  clean                       - Stop all services and clean volumes"
