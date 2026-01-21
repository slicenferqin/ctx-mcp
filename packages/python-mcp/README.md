# Context Engineering MCP Server

这是一个符合 **Model Context Protocol (MCP)** 标准的服务器，旨在为 Claude Desktop、Cursor 或其他 AI 助手提供"外部记忆"和"上下文管理"能力。

它实现了 [Context Engineering](./ai-programming-best-practices.md) 的核心理念，允许 AI 像操作系统一样管理自己的工作区状态。

## ✨ 功能

这个插件为你的 AI 助手添加了以下能力（Tools）：

1.  **`context_init`**: 初始化 `.ai/skills` 和 `.agent_memory` 目录结构。
2.  **`context_state`**: 获取当前工作区的"快照"（包含目录树、Git状态、当前目标）。
3.  **`context_save_observation`**: 将长输出（如日志、API响应）保存到文件，只返回摘要。
4.  **`context_read_observation`**: 按需读取之前保存的观察结果。

## 📦 安装与配置

### 1. 作为 Python 包安装

```bash
# 从 PyPI 安装
pip install ctx-engine-mcp
```

### 2. 配置 Claude Desktop

编辑你的 Claude Desktop 配置文件（通常位于 `~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "context-engineering": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "ctx-engine-mcp",
        "context-mcp"
      ]
    }
  }
}
```

或者使用系统 Python：

```json
{
  "mcpServers": {
    "context-engineering": {
      "command": "python3",
      "args": ["-m", "context_mcp.server"]
    }
  }
}
```

### 3. 配置 Cursor (即将支持)

Cursor 目前正在积极集成 MCP，配置方式与 Claude Desktop 类似。

## 🛠️ 使用示例

一旦配置完成，你可以在对话中直接告诉 Claude：

> "初始化一下上下文环境" -> Claude 会调用 `context_init`

> "现在的项目状态是什么？" -> Claude 会调用 `context_state`

> "运行 npm install 并帮我分析错误，输出可能很长，请注意使用外部记忆" -> Claude 会运行命令并使用 `context_save_observation` 保存结果。
