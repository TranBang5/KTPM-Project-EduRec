#!/bin/bash
# Script to run Locust load tests

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
HOST="${1:-http://api-gateway:5000}"
USERS="${2:-50}"
SPAWN_RATE="${3:-5}"
RUN_TIME="${4:-5m}"

echo -e "${GREEN}Starting Locust Load Test${NC}"
echo "=========================================="
echo "Host: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE users/second"
echo "Run Time: $RUN_TIME"
echo "=========================================="

# Create reports directory if it doesn't exist
mkdir -p reports

# Generate timestamp for report files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="reports/locust_${TIMESTAMP}.html"
CSV_PREFIX="reports/locust_${TIMESTAMP}"

# Run Locust test
docker compose run --rm locust locust \
  --host="$HOST" \
  --users="$USERS" \
  --spawn-rate="$SPAWN_RATE" \
  --run-time="$RUN_TIME" \
  --headless \
  --html="$REPORT_FILE" \
  --csv="$CSV_PREFIX" \
  --loglevel=INFO

echo -e "\n${GREEN}Test completed!${NC}"
echo "Report: $REPORT_FILE"
echo "CSV files: ${CSV_PREFIX}_*.csv"

