#!/bin/bash
#
# Setup daily 6am cron job for EnterpriseCashFlow analysis
#
# Usage: bash scripts/setup_cron.sh
# This script installs a cron job to run the analysis pipeline daily at 6am

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}EnterpriseCashFlow - Daily Cron Job Setup${NC}"
echo "================================================"
echo ""

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    CRON_CMD="0 6 * * * cd $PROJECT_DIR && /usr/local/bin/python3 -m entcash run --input data/imports --output data/results"
    echo -e "${YELLOW}Detected macOS${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CRON_CMD="0 6 * * * cd $PROJECT_DIR && python3 -m entcash run --input data/imports --output data/results"
    echo -e "${YELLOW}Detected Linux${NC}"
else
    echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
    exit 1
fi

echo ""
echo "Project directory: $PROJECT_DIR"
echo ""
echo "Cron job to be installed:"
echo "  Time: 6:00 AM daily"
echo "  Command: ${CRON_CMD}"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "entcash run"; then
    echo -e "${YELLOW}Warning: Cron job already exists for entcash${NC}"
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    # Remove existing cron job
    (crontab -l 2>/dev/null | grep -v "entcash run" | crontab -) || true
fi

# Install new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo -e "${GREEN}Cron job installed successfully!${NC}"
echo ""
echo "To view installed cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e  (and manually delete the line)"
echo ""
echo "Logs will be available in:"
echo "  $PROJECT_DIR/logs/cron.log"
echo ""

# Verify installation
echo "Verifying installation..."
if crontab -l 2>/dev/null | grep -q "entcash run"; then
    echo -e "${GREEN}✓ Cron job verified${NC}"
else
    echo -e "${RED}✗ Failed to install cron job${NC}"
    exit 1
fi

exit 0
