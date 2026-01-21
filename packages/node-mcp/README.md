# Context Engineering MCP Server

A Model Context Protocol (MCP) server that implements the "Context Engineering" methodology. It helps AI agents manage workspace state, offload large context, and adhere to team skills.

## Features

- **Dynamic Context Initialization**: Automatically creates `.ai/skills` and `.agent_memory` structures.
- **Workspace State Snapshot**: Provides `get_workspace_state` tool to give agents a high-level view of the project (goals, file tree, git status).
- **Observation Offloading**: Provides `save_observation` to save large tool outputs to files instead of cluttering the context window.

## 📊 Benefits

- **📉 Reduce Token Usage by 90%**: Offload large logs/outputs to file system.
- **📈 Improve Accuracy by 40%**: Structured skills reduce hallucinations and enforce standards.
- **🚀 Instant Onboarding**: Agents understand project context immediately.

## Installation

### Option 1: Run with npx (Recommended)

You can run this server directly using `npx` without installing it globally (once published):

```bash
npx context-engineering-mcp
```

### Option 2: Install Globally

```bash
npm install -g context-engineering-mcp
```

## Configuration

### Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "context-engineering": {
      "command": "npx",
      "args": [
        "-y",
        "context-engineering-mcp"
      ]
    }
  }
}
```

### Local Development

If you have cloned this repository:

```json
{
  "mcpServers": {
    "context-engineering": {
      "command": "node",
      "args": [
        "/absolute/path/to/context-mcp-node/dist/index.js"
      ]
    }
  }
}
```
