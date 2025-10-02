# Reverse Dependency Testing

This directory contains all reverse dependency testing components for the AI Workflows platform.

## Container Builds

The `container/Containerfile` provides several build targets:

- **production** (default): Official Goose releases
- **debug**: Custom Goose builds with patches applied
- **source-build**: Build Goose from source with custom patches

## Automation Recipes

The `recipes/` directory contains YAML workflow for testing reverse dependencies of a package.

## Usage

Navigate to the revdeps_tester directory and use the Makefile:

```bash
# Build the containers
make build

# Run interactive revdeps_tester session
make run-revdeps-tester

# Run specific recipe
make test-reverse-dependencies PACKAGE=podman
```

## Configuration

Edit `container/revdeps_tester-config.yaml` to configure:
- LLM provider and model settings
- MCP server connections
- Tool configurations

## Setup

1. **Copy template files:**
   ```bash
   make config
   ```

2. **Configure your environment variables in `.secrets/`:**
   - `goose.env` - goose and API configurations
   - `mcp-testing-farm.env` - Testing Farm API token
   - `testing-farm-sse-bridge.env` - Testing Farm SSE Bridge configuration

3. **Build and run:**
   ```bash
   make build
   make run-revdeps-tester
   ```

**Note**: This Goose-based automation is deprecated and will soon be replaced with a BeeAI based workflow.
