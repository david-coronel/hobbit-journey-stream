#!/bin/bash
# Run the event generator for a specific gap or batch of gaps.
# Usage:
#   ./run_generator.sh gap_canon_044_canon_045
#   ./run_generator.sh --all-small-gaps

set -e

GAP_ID="${1:-}"
EXTRA_ARGS="${@:2}"

if [ -z "$GAP_ID" ]; then
    echo "Usage: $0 <gap_id> [extra_args]"
    echo "   or: $0 --all-small-gaps"
    echo "   or: $0 --all-travel-gaps"
    exit 1
fi

# Ensure virtual environment or python3 is available
PYTHON="${PYTHON:-python3}"

echo "[run_generator] Initializing database..."
$PYTHON scripts/event_generator.py --init-db

echo "[run_generator] Starting generation for target: $GAP_ID $EXTRA_ARGS"
$PYTHON scripts/event_generator.py --gap-id "$GAP_ID" $EXTRA_ARGS

echo "[run_generator] Done."
