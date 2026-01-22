# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-21

### Added
- **Lazy Loading**: All MCP tools now auto-initialize the context structure on first use
  - `get_workspace_state`, `save_observation`, and `read_observation` automatically create `.ai/skills/` and `.agent_memory/` directories if they don't exist
  - Users no longer need to explicitly call `initialize_context_system`
  - Seamless integration with existing projects

### Changed
- Improved user experience: tools work transparently without manual initialization
- `initialize_context_system` is now optional - kept for explicit initialization scenarios

## [0.1.0] - 2026-01-21

### Added

#### Core Features
- **Python MCP Server** (`ctx-engine-mcp` on PyPI)
  - `initialize_context_system`: Initialize `.ai/skills` and `.agent_memory` structure
  - `get_workspace_state`: Generate workspace snapshots with goals, file tree, and git status
  - `save_observation`: Save long outputs to external memory
  - `read_observation`: Read previously saved observations

- **Node.js MCP Server** (`context-engineering-mcp` on npm)
  - Same feature set as Python MCP
  - TypeScript implementation with full type safety
  - Zero-dependency binary distribution

- **CLI Tool** (`ctx.py`)
  - `ctx init`: Initialize context structure
  - `ctx state`: Generate workspace state snapshot
  - `ctx wrap`: Run commands and capture long outputs
  - `ctx read`: Read saved observation files

#### Documentation
- **ai-programming-best-practices.md**: Comprehensive guide on context engineering methodology
- **file-system-as-external-memory.md**: Comparison of different implementations (Cursor, Manus, InfiAgent)
- **cognitive-science-of-context-engineering.md**: Theoretical foundations from cognitive science perspective

#### Infrastructure
- MIT License
- Comprehensive README with installation instructions
- Package metadata for npm and PyPI publication

### Security
- Added path traversal protection in `read_observation` (Python MCP)
- Restricted file access to `.agent_memory/observations/` directory only

### Fixed
- Added missing `main()` entry point to Python MCP server
- Added `__init__.py` to make Python package installable
- Unified MCP tool naming across Python and Node implementations
- Added `prepare` and `prepublishOnly` scripts to Node package
- Added directory creation failsafe to CLI `wrap` command
- Removed unused imports from CLI tool

### Changed
- Python package name: `context-mcp` → `ctx-engine-mcp` (for PyPI)
- Tool naming: `init_context` → `initialize_context_system` (unified across implementations)

## [Unreleased]

### Planned
- Usage examples and tutorials
- Integration tests
- GitHub Actions CI/CD
- Additional MCP tools for advanced context management

---

[0.1.1]: https://github.com/slicenferqin/ctx-mcp/releases/tag/v0.1.1
[0.1.0]: https://github.com/slicenferqin/ctx-mcp/releases/tag/v0.1.0
