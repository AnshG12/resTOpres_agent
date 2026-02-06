#!/bin/bash
# Simple presentation generator wrapper

echo "🎯 LaTeX to Beamer Presentation Generator"
echo "=========================================="
echo ""

# Check if folder argument provided
if [ -z "$1" ]; then
    echo "Usage: ./run.sh <paper_folder> [options]"
    echo ""
    echo "Examples:"
    echo "  ./run.sh arXiv-2602.04843v1"
    echo "  ./run.sh my_paper --title 'My Title'"
    echo ""
    exit 1
fi

# Run the agent
uv run python -m src.agent.cli make-presentation "$@"
