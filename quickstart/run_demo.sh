#!/usr/bin/env bash
# Five-minute, dependency-free Table 3 reproduction.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 quickstart/run_demo.py "$@"
