from mcp.server.fastmcp import FastMCP
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
import json

# Initialize FastMCP server
mcp = FastMCP("context-engineering")

# --- Constants & Templates ---
AI_DIR = Path(".ai")
SKILLS_DIR = AI_DIR / "skills"
MEMORY_DIR = Path(".agent_memory")
OBSERVATIONS_DIR = MEMORY_DIR / "observations"
CACHE_DIR = MEMORY_DIR / "context_cache"

CODING_STANDARDS_TEMPLATE = """# Coding Standards

## General Principles
- **Clarity over cleverness**: Write code that is easy to understand.
- **Consistency**: Follow the existing style of the codebase.
- **DRY (Don't Repeat Yourself)**: Extract common logic.

## Naming Conventions
- Variables: `camelCase`
- Functions: `camelCase`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`

## Error Handling
- Always handle errors explicitly.
- Use custom error classes for domain-specific errors.
"""

GOALS_TEMPLATE = """# Current Goals

## Main Objective
Describe the main objective here.

## Tasks
- [ ] Task 1
- [ ] Task 2
"""

STATE_TEMPLATE = """# Workspace State
Updated: {timestamp}

## Current Goals
{goals}

## Recent Changes
{changes}

## Directory Structure (Depth: 2)
{structure}
"""

# --- Helpers ---

def _get_tree(dir_path: str = ".", max_depth: int = 2) -> str:
    """Generate a simplified directory tree string."""
    def generate_lines(path, prefix="", depth=0):
        if depth >= max_depth:
            return []
        
        lines = []
        try:
            entries = sorted(os.listdir(path), key=lambda s: (not os.path.isdir(os.path.join(path, s)), s))
            entries = [e for e in entries if not e.startswith('.')]
            
            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    if entry in ["node_modules", "venv", "__pycache__", "dist", "build", ".git"]:
                         lines.append(f"{prefix}{connector}{entry}/ ...")
                    else:
                        lines.append(f"{prefix}{connector}{entry}/")
                        extension = "    " if is_last else "│   "
                        lines.extend(generate_lines(full_path, prefix + extension, depth + 1))
                else:
                    lines.append(f"{prefix}{connector}{entry}")
        except PermissionError:
            pass
        return lines

    return "\n".join(generate_lines(dir_path))

def _get_git_status() -> str:
    """Get concise git status."""
    try:
        changes = subprocess.check_output(["git", "status", "--short"], stderr=subprocess.DEVNULL, text=True).strip()
        if changes:
            return f"```\n{changes}\n```"
        return "Working tree clean."
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Not a git repository."

# --- Tools ---

@mcp.tool()
def init_context() -> str:
    """
    Initialize the Context Engineering directory structure (.ai/skills, .agent_memory).
    Use this when starting a new project or if the context structure is missing.
    """
    results = []
    
    # Create directories
    for d in [SKILLS_DIR, OBSERVATIONS_DIR, CACHE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        results.append(f"✅ Created directory: {d}")
        
    # Create templates
    skills_file = SKILLS_DIR / "coding-standards.md"
    if not skills_file.exists():
        skills_file.write_text(CODING_STANDARDS_TEMPLATE)
        results.append(f"✅ Created skill: {skills_file}")
        
    goals_file = MEMORY_DIR / "goals.md"
    if not goals_file.exists():
        goals_file.write_text(GOALS_TEMPLATE)
        results.append(f"✅ Created memory: {goals_file}")
        
    gitignore = MEMORY_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n!.gitignore\n!goals.md\n")
        results.append(f"✅ Created .gitignore for memory")
        
    return "\n".join(results)

@mcp.tool()
def get_workspace_state() -> str:
    """
    Get a snapshot of the current workspace state, including goals, file structure, and git status.
    Call this tool to orient yourself before starting a task or when context is lost.
    """
    # 1. Read goals
    goals_file = MEMORY_DIR / "goals.md"
    goals_content = goals_file.read_text() if goals_file.exists() else "No goals defined."
    
    # 2. Get structure and changes
    structure = _get_tree()
    changes = _get_git_status()
    
    # 3. Generate Report
    report = STATE_TEMPLATE.format(
        timestamp=datetime.now().isoformat(),
        goals=goals_content.strip(),
        changes=changes,
        structure=structure.strip()
    )
    
    # Optional: Save to file for persistence
    (MEMORY_DIR / "state.md").write_text(report)
    
    return report

@mcp.tool()
def save_observation(content: str, summary: str, filename_hint: str = "observation") -> str:
    """
    Save large text content (logs, analysis, code) to the file system memory and return a reference.
    Use this tool when output is too long (>20 lines) to avoid cluttering the context window.
    
    Args:
        content: The full content to save.
        summary: A brief summary of what this content is.
        filename_hint: A short string to use in the filename (e.g., 'npm_install_log').
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_hint = "".join(c for c in filename_hint if c.isalnum() or c in "_-")[:30]
    filename = f"{timestamp}_{safe_hint}.txt"
    file_path = OBSERVATIONS_DIR / filename
    
    # Ensure dir exists
    OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path.write_text(content)
    
    return f"""
✅ Content saved to external memory.
Summary: {summary}
File Path: {file_path}
Size: {len(content)} chars
    """.strip()

@mcp.tool()
def read_observation(file_path: str) -> str:
    """
    Read the full content of a previously saved observation file.
    Use this when you need the details of a file referenced in a summary.
    
    Args:
        file_path: The absolute or relative path to the observation file.
    """
    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found at {file_path}"
    
    return path.read_text()

if __name__ == "__main__":
    mcp.run()
