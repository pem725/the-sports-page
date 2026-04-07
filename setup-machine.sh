#!/bin/bash
# setup-machine.sh — Set up The Sports Page on a new machine (Linux or Mac)
#
# Run this ONCE on each new machine after cloning the repo.
# It creates the symlinks and copies the skill files that aren't in git.
#
# Usage:
#   git clone https://github.com/pem725/the-sports-page.git ~/GitTemp/the-sports-page
#   cd ~/GitTemp/the-sports-page
#   ./setup-machine.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/sports-stat-storyteller"
PROJECT_DIR="$HOME/.claude/projects"

echo "=== The Sports Page — Machine Setup ==="
echo "Repo: $REPO_DIR"
echo "OS: $(uname -s)"
echo ""

# 1. Create the skill symlink
if [ -L "$SKILL_DIR" ]; then
    echo "✓ Skill symlink already exists: $SKILL_DIR → $(readlink "$SKILL_DIR")"
elif [ -d "$SKILL_DIR" ]; then
    echo "⚠ $SKILL_DIR exists as a directory (not a symlink)"
    echo "  If this is a fresh setup, remove it first: rm -rf $SKILL_DIR"
    echo "  Then re-run this script."
    exit 1
else
    mkdir -p "$HOME/.claude/skills"
    ln -s "$REPO_DIR" "$SKILL_DIR"
    echo "✓ Created skill symlink: $SKILL_DIR → $REPO_DIR"
fi

# 2. Create SKILL.md if missing (gitignored — won't be in the clone)
if [ ! -f "$REPO_DIR/SKILL.md" ]; then
    echo "⚠ SKILL.md not found (it's gitignored)."
    echo "  Copy it from your other machine, or the skill won't trigger."
    echo "  On your Linux box: scp ~/.claude/skills/sports-stat-storyteller/SKILL.md user@mac:~/GitTemp/the-sports-page/"
else
    echo "✓ SKILL.md present"
fi

# 3. Create CLAUDE.md if missing
if [ ! -f "$REPO_DIR/CLAUDE.md" ]; then
    echo "⚠ CLAUDE.md not found (it's gitignored)."
    echo "  Copy it from your other machine for project context."
else
    echo "✓ CLAUDE.md present"
fi

# 4. Check for the .skill file
if [ ! -f "$REPO_DIR/sports-stat-storyteller.skill" ]; then
    echo "⚠ sports-stat-storyteller.skill not found (it's gitignored)."
    echo "  Copy it from your other machine if you need the packaged skill."
else
    echo "✓ sports-stat-storyteller.skill present"
fi

# 5. Ensure publish.sh is executable
chmod +x "$REPO_DIR/publish.sh" 2>/dev/null && echo "✓ publish.sh is executable"

# 6. Check git remote
REMOTE=$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null)
echo "✓ Git remote: $REMOTE"

# 7. Check gh CLI
if command -v gh &>/dev/null; then
    echo "✓ GitHub CLI (gh) installed"
    gh auth status 2>&1 | head -1 | sed 's/^/  /'
else
    echo "⚠ GitHub CLI (gh) not installed — needed for publish workflow"
fi

# 8. Summary
echo ""
echo "=== Setup Complete ==="
echo "Workflow:"
echo "  cd ~/GitTemp/the-sports-page"
echo "  git pull                           # get latest from other machine"
echo "  ./publish.sh queue/FILENAME.html   # publish an issue"
echo ""
echo "To copy gitignored files from your Linux box:"
echo "  scp linux:~/.claude/skills/sports-stat-storyteller/SKILL.md ."
echo "  scp linux:~/.claude/skills/sports-stat-storyteller/CLAUDE.md ."
echo "  scp linux:~/.claude/skills/sports-stat-storyteller/sports-stat-storyteller.skill ."
