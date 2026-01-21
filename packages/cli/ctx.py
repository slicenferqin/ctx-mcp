#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
import json
from datetime import datetime

# --- Configuration ---
AI_DIR = Path(".ai")
SKILLS_DIR = AI_DIR / "skills"
MEMORY_DIR = Path(".agent_memory")
OBSERVATIONS_DIR = MEMORY_DIR / "observations"
CACHE_DIR = MEMORY_DIR / "context_cache"

# --- Templates ---

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

# --- Commands ---

def cmd_init(args):
    """Initialize the Context Engineering directory structure."""
    print("🚀 Initializing Context Engineering structure...")
    
    dirs = [SKILLS_DIR, OBSERVATIONS_DIR, CACHE_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {d}")
        
    # Create templates
    skills_file = SKILLS_DIR / "coding-standards.md"
    if not skills_file.exists():
        skills_file.write_text(CODING_STANDARDS_TEMPLATE)
        print(f"✅ Created skill: {skills_file}")
        
    goals_file = MEMORY_DIR / "goals.md"
    if not goals_file.exists():
        goals_file.write_text(GOALS_TEMPLATE)
        print(f"✅ Created memory: {goals_file}")
        
    # Create .gitignore for memory
    gitignore = MEMORY_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n!.gitignore\n!goals.md\n")
        print(f"✅ Created .gitignore for memory (ignoring transient files)")

    print("\n✨ Initialization complete! You are ready to engineer context.")

def cmd_state(args):
    """Generate a snapshot of the current workspace state."""
    print("📸 Taking workspace snapshot...")
    
    # 1. Read goals
    goals_file = MEMORY_DIR / "goals.md"
    goals_content = goals_file.read_text() if goals_file.exists() else "No goals defined."
    
    # 2. Get file structure (simplified tree)
    # Python-native tree implementation
    def generate_tree(dir_path, prefix="", depth=0, max_depth=2):
        if depth >= max_depth:
            return []
        
        lines = []
        try:
            # Sort directories first, then files
            entries = sorted(os.listdir(dir_path), key=lambda s: (not os.path.isdir(os.path.join(dir_path, s)), s))
            entries = [e for e in entries if not e.startswith('.')] # Skip hidden files by default
            
            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                
                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    if entry in ["node_modules", "venv", "__pycache__", "dist", "build"]:
                         lines.append(f"{prefix}{connector}{entry}/ ...")
                    else:
                        lines.append(f"{prefix}{connector}{entry}/")
                        extension = "    " if is_last else "│   "
                        lines.extend(generate_tree(full_path, prefix + extension, depth + 1, max_depth))
                else:
                    lines.append(f"{prefix}{connector}{entry}")
        except PermissionError:
            pass
        return lines

    tree_lines = generate_tree(".")
    structure = "\n".join(tree_lines)
        
    # 3. Get recent changes (git status)
    try:
        # Use git to get recent changes if available
        changes_output = subprocess.check_output(["git", "status", "--short"], stderr=subprocess.DEVNULL, text=True)
        if changes_output:
            changes = "```\n" + changes_output + "```"
        else:
            changes = "Working tree clean."
        
        # Get last commit
        last_commit = subprocess.check_output(["git", "log", "-1", "--oneline"], stderr=subprocess.DEVNULL, text=True).strip()
        changes += f"\n\nLast commit: {last_commit}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        changes = "Not a git repository."

    # 4. Generate State Report
    report = STATE_TEMPLATE.format(
        timestamp=datetime.now().isoformat(),
        goals=goals_content.strip(),
        changes=changes.strip(),
        structure=structure.strip()
    )
    
    # Output to file and stdout
    output_file = MEMORY_DIR / "state.md"
    output_file.write_text(report)
    print(f"✅ State saved to: {output_file}")
    
    if args.print:
        print("\n" + "="*20 + " STATE PREVIEW " + "="*20)
        print(report)
        print("="*55)

def cmd_wrap(args):
    """Run a command and capture its output to memory if it's too long."""
    cmd = args.command
    if not cmd:
        print("Error: No command provided.")
        return

    print(f"▶️  Running: {' '.join(cmd)}")

    start_time = time.time()
    result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
    duration = time.time() - start_time

    stdout = result.stdout
    stderr = result.stderr
    combined = stdout + stderr

    # Threshold for "long output" (e.g., 1000 chars or 20 lines)
    is_long = len(combined) > 1000 or combined.count('\n') > 20

    if is_long or args.force:
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cmd_slug = "_".join(cmd)[:30].replace("/", "_") # simplistic slug
        filename = f"{timestamp}_{cmd_slug}.log"
        file_path = OBSERVATIONS_DIR / filename

        # Construct content
        cmd_str = ' '.join(args.command)
        content = f"Command: {cmd_str}\n\n=== STDOUT ===\n{stdout}\n\n=== STDERR ===\n{stderr}"
        file_path.write_text(content)

        # Generate summary for stdout
        line_count = combined.count('\n')
        summary = f"""
✅ Command finished in {duration:.2f}s (Exit Code: {result.returncode})
📦 Output saved to: {file_path}
📊 Size: {len(combined)} chars, {line_count} lines

Preview (Head 10 lines):
{chr(10).join(combined.splitlines()[:10])}
...
"""
        print(summary)
    else:
        # Just print it if it's short
        print(combined)

def cmd_read(args):
    """Read a previously saved observation file."""
    filename = args.filename

    # Try to find the file
    file_path = OBSERVATIONS_DIR / filename

    if not file_path.exists():
        # Try to find by partial match
        try:
            matches = list(OBSERVATIONS_DIR.glob(f"*{filename}*"))
            if matches:
                file_path = matches[0]
                print(f"📄 Found: {file_path.name}")
            else:
                print(f"❌ Error: No observation file matching '{filename}' found.")
                print(f"Available files in {OBSERVATIONS_DIR}:")
                for f in OBSERVATIONS_DIR.glob("*.log"):
                    print(f"  - {f.name}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return

    # Read and display
    try:
        content = file_path.read_text()

        if args.head:
            lines = content.splitlines()
            print(f"📄 {file_path.name} (showing first {args.head} lines):\n")
            print('\n'.join(lines[:args.head]))
        elif args.tail:
            lines = content.splitlines()
            print(f"📄 {file_path.name} (showing last {args.tail} lines):\n")
            print('\n'.join(lines[-args.tail:]))
        else:
            print(f"📄 {file_path.name}:\n")
            print(content)

    except Exception as e:
        print(f"❌ Error reading file: {e}")

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Context Engineering CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    parser_init = subparsers.add_parser("init", help="Initialize directory structure")
    parser_init.set_defaults(func=cmd_init)
    
    # State command
    parser_state = subparsers.add_parser("state", help="Generate workspace state snapshot")
    parser_state.add_argument("--print", "-p", action="store_true", help="Print state to stdout")
    parser_state.set_defaults(func=cmd_state)
    
    # Wrap command
    parser_wrap = subparsers.add_parser("wrap", help="Run command and capture output")
    parser_wrap.add_argument("command", nargs=argparse.REMAINDER, help="The command to run")
    parser_wrap.add_argument("--force", "-f", action="store_true", help="Force save to file even if short")
    parser_wrap.set_defaults(func=cmd_wrap)

    # Read command
    parser_read = subparsers.add_parser("read", help="Read a saved observation file")
    parser_read.add_argument("filename", help="Filename or partial match to read")
    parser_read.add_argument("--head", type=int, help="Show only first N lines")
    parser_read.add_argument("--tail", type=int, help="Show only last N lines")
    parser_read.set_defaults(func=cmd_read)

    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
