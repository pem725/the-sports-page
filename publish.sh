#!/bin/bash
# publish.sh — Move an issue from queue/ or reserve/ to published/ and go live
#
# Usage:
#   ./publish.sh queue/005-draft-combinatorics.html
#   ./publish.sh reserve/cfb-coach-carousel.html
#
# What it does:
#   1. Moves the file to published/
#   2. Stages the change
#   3. Commits with a publish message
#   4. Pushes to GitHub (goes live on GitHub Pages)
#
# NOTE: You still need to manually add the issue to index.html before running.
#       (Or ask Claude to do it.)

set -e

if [ -z "$1" ]; then
    echo "Usage: ./publish.sh <path-to-issue>"
    echo ""
    echo "Queue (ready to publish):"
    ls queue/ 2>/dev/null || echo "  (empty)"
    echo ""
    echo "Reserve (evergreen, no date):"
    ls reserve/ 2>/dev/null || echo "  (empty)"
    echo ""
    echo "Published:"
    ls published/ 2>/dev/null || echo "  (empty)"
    exit 1
fi

SOURCE="$1"
FILENAME=$(basename "$SOURCE")

if [ ! -f "$SOURCE" ]; then
    echo "Error: $SOURCE not found"
    exit 1
fi

if [ -f "published/$FILENAME" ]; then
    echo "Error: published/$FILENAME already exists"
    exit 1
fi

echo "Publishing: $SOURCE → published/$FILENAME"
git mv "$SOURCE" "published/$FILENAME"
git add index.html published/"$FILENAME"
git commit -m "Publish: $FILENAME"
git push

echo ""
echo "Live at: https://pem725.github.io/the-sports-page/published/$FILENAME"
echo "Done."
