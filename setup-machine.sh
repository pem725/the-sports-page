#!/bin/bash
# setup-machine.sh — Set up The Sports Page on a new machine (Linux or Mac)
#
# Run this ONCE on each new machine after cloning the repo.
# It creates the skill symlink and configures git to enforce fast-forward
# pulls in this repo (so a stale local clone fails loudly instead of
# silently merging out-of-date state).
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

# 2. Enforce fast-forward-only pulls in this repo
# This means `git pull` will fail loudly on divergence rather than silently
# merge — preventing the "stale local clone published as if it were current"
# class of failure that bit us on 2026-05-10. See CLAUDE.md "Step 0".
git -C "$REPO_DIR" config --local pull.ff only
echo "✓ Configured pull.ff=only (fast-forward only) for this repo"

# 3. Ensure publish.sh is executable
chmod +x "$REPO_DIR/publish.sh" 2>/dev/null && echo "✓ publish.sh is executable"

# 4. Check git remote
REMOTE=$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null)
echo "✓ Git remote: $REMOTE"

# 5. Check gh CLI
if command -v gh &>/dev/null; then
    echo "✓ GitHub CLI (gh) installed"
    gh auth status 2>&1 | head -1 | sed 's/^/  /'
else
    echo "⚠ GitHub CLI (gh) not installed — needed for publish workflow"
fi

# 6. Summary
echo ""
echo "=== Setup Complete ==="
echo "Workflow:"
echo "  cd ~/GitTemp/the-sports-page"
echo "  git fetch origin main && git pull --ff-only   # always before any work"
echo "  ./publish.sh queue/FILENAME.html              # publish an issue"
echo ""
echo "Note: pull.ff=only is set for this repo. If a pull is rejected as"
echo "non-fast-forward, you have local commits that diverge from origin."
echo "Inspect with 'git log HEAD..origin/main' and reconcile deliberately."
