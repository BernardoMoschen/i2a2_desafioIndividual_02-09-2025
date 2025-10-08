#!/bin/sh
set -euo pipefail

APP_USER="${APP_USER:-agent}"
DATA_DIR="${DATA_DIR:-/app/data}"
REPORTS_DIR="${REPORTS_DIR:-/app/reports}"


echo "Container entrypoint removed. This repository no longer uses container-based defaults."
exit 0
