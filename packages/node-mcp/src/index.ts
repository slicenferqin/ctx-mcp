#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";
import { exec } from "child_process";
import util from "util";
import { fileURLToPath } from "url";

const execAsync = util.promisify(exec);

// --- Configuration ---
const CWD = process.cwd();
const AI_DIR = path.join(CWD, ".ai");
const SKILLS_DIR = path.join(AI_DIR, "skills");
const MEMORY_DIR = path.join(CWD, ".agent_memory");
const OBSERVATIONS_DIR = path.join(MEMORY_DIR, "observations");
const CACHE_DIR = path.join(MEMORY_DIR, "context_cache");
const GOALS_FILE = path.join(MEMORY_DIR, "goals.md");
const STATE_FILE = path.join(MEMORY_DIR, "state.md");

// --- Templates ---
const CODING_STANDARDS_TEMPLATE = `# Coding Standards

## General Principles
- **Clarity over cleverness**: Write code that is easy to understand.
- **Consistency**: Follow the existing style of the codebase.
- **DRY (Don't Repeat Yourself)**: Extract common logic.

## Naming Conventions
- Variables: \`camelCase\`
- Functions: \`camelCase\`
- Classes: \`PascalCase\`
- Constants: \`UPPER_CASE\`

## Error Handling
- Always handle errors explicitly.
- Use custom error classes for domain-specific errors.
`;

const GOALS_TEMPLATE = `# Current Goals

## Main Objective
Describe the main objective here.

## Tasks
- [ ] Task 1
- [ ] Task 2
`;

const STATE_TEMPLATE = `# Workspace State
Updated: {timestamp}

## Current Goals
{goals}

## Recent Changes
{changes}

## Directory Structure (Depth: 2)
{structure}
`;

// --- Helper Functions ---

async function ensureDirectory(dirPath: string) {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (error) {
    // Ignore if exists
  }
}

async function generateTree(dirPath: string, prefix = "", depth = 0, maxDepth = 2): Promise<string[]> {
  if (depth >= maxDepth) return [];

  const lines: string[] = [];
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    
    // Sort directories first, then files
    entries.sort((a, b) => {
      if (a.isDirectory() && !b.isDirectory()) return -1;
      if (!a.isDirectory() && b.isDirectory()) return 1;
      return a.name.localeCompare(b.name);
    });

    const filteredEntries = entries.filter(e => !e.name.startsWith('.'));

    for (let i = 0; i < filteredEntries.length; i++) {
      const entry = filteredEntries[i];
      const isLast = i === filteredEntries.length - 1;
      const connector = isLast ? "└── " : "├── ";
      
      if (entry.isDirectory()) {
        if (["node_modules", "venv", "__pycache__", "dist", "build", ".git"].includes(entry.name)) {
           lines.push(`${prefix}${connector}${entry.name}/ ...`);
        } else {
          lines.push(`${prefix}${connector}${entry.name}/`);
          const extension = isLast ? "    " : "│   ";
          lines.push(...await generateTree(path.join(dirPath, entry.name), prefix + extension, depth + 1, maxDepth));
        }
      } else {
        lines.push(`${prefix}${connector}${entry.name}`);
      }
    }
  } catch (error) {
    // Ignore permission errors etc
  }
  return lines;
}

// --- Server Implementation ---

const server = new Server(
  {
    name: "context-engineering-mcp",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "initialize_context_system",
        description: "Initialize the Context Engineering directory structure (.ai/skills, .agent_memory)",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "get_workspace_state",
        description: "Generate a snapshot of the current workspace state (goals, file structure, git status)",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "save_observation",
        description: "Save large tool output or observation to a file in .agent_memory",
        inputSchema: {
          type: "object",
          properties: {
            command: {
              type: "string",
              description: "The command that produced the output",
            },
            content: {
              type: "string",
              description: "The full content to save",
            },
          },
          required: ["command", "content"],
        },
      },
      {
        name: "read_observation",
        description: "Read a previously saved observation file",
        inputSchema: {
          type: "object",
          properties: {
            filename: {
              type: "string",
              description: "The filename of the observation to read",
            },
          },
          required: ["filename"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (request.params.name) {
    case "initialize_context_system": {
      await ensureDirectory(SKILLS_DIR);
      await ensureDirectory(OBSERVATIONS_DIR);
      await ensureDirectory(CACHE_DIR);

      // Create coding standards
      const skillsFile = path.join(SKILLS_DIR, "coding-standards.md");
      try {
        await fs.access(skillsFile);
      } catch {
        await fs.writeFile(skillsFile, CODING_STANDARDS_TEMPLATE);
      }

      // Create goals
      try {
        await fs.access(GOALS_FILE);
      } catch {
        await fs.writeFile(GOALS_FILE, GOALS_TEMPLATE);
      }

      // Create gitignore
      const gitignoreFile = path.join(MEMORY_DIR, ".gitignore");
      try {
        await fs.access(gitignoreFile);
      } catch {
        await fs.writeFile(gitignoreFile, "*\n!.gitignore\n!goals.md\n");
      }

      return {
        content: [
          {
            type: "text",
            text: "Context Engineering system initialized successfully.",
          },
        ],
      };
    }

    case "get_workspace_state": {
      // 1. Read goals
      let goalsContent = "No goals defined.";
      try {
        goalsContent = await fs.readFile(GOALS_FILE, "utf-8");
      } catch {}

      // 2. File structure
      const treeLines = await generateTree(CWD);
      const structure = treeLines.join("\n");

      // 3. Recent changes
      let changes = "Not a git repository.";
      try {
        const { stdout: status } = await execAsync("git status --short");
        const { stdout: lastCommit } = await execAsync("git log -1 --oneline");
        changes = status ? "```\n" + status + "```" : "Working tree clean.";
        changes += `\n\nLast commit: ${lastCommit.trim()}`;
      } catch {}

      const report = STATE_TEMPLATE
        .replace("{timestamp}", new Date().toISOString())
        .replace("{goals}", goalsContent.trim())
        .replace("{changes}", changes.trim())
        .replace("{structure}", structure.trim());

      await fs.writeFile(STATE_FILE, report);

      return {
        content: [
          {
            type: "text",
            text: report,
          },
        ],
      };
    }

    case "save_observation": {
      const { command, content } = request.params.arguments as { command: string; content: string };
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const cmdSlug = command.replace(/[^a-zA-Z0-9]/g, "_").slice(0, 30);
      const filename = `${timestamp}_${cmdSlug}.log`;
      const filePath = path.join(OBSERVATIONS_DIR, filename);

      const fileContent = `Command: ${command}\n\n=== CONTENT ===\n${content}`;
      
      await ensureDirectory(OBSERVATIONS_DIR);
      await fs.writeFile(filePath, fileContent);

      const summary = `
✅ Output saved to: ${path.relative(CWD, filePath)}
📊 Size: ${content.length} chars, ${content.split('\n').length} lines
Preview:
${content.split('\n').slice(0, 10).join('\n')}
...
`;

      return {
        content: [
          {
            type: "text",
            text: summary,
          },
        ],
      };
    }

    case "read_observation": {
      const { filename } = request.params.arguments as { filename: string };
      // Security check: prevent directory traversal
      const safeFilename = path.basename(filename);
      const filePath = path.join(OBSERVATIONS_DIR, safeFilename);

      try {
        const content = await fs.readFile(filePath, "utf-8");
        return {
          content: [
            {
              type: "text",
              text: content,
            },
          ],
        };
      } catch (error) {
        return {
          isError: true,
          content: [
            {
              type: "text",
              text: `Error reading file: ${error}`,
            },
          ],
        };
      }
    }

    default:
      throw new Error("Unknown tool");
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
