#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}        Project Setup Script            ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# --- Python venv ---
echo -e "${CYAN}[1/3] Creating Python virtual environment...${NC}"
python3 -m venv .venv
echo -e "      Virtual environment created at ${CYAN}.venv/${NC}"
echo ""

# --- Activate venv ---
source .venv/bin/activate

# --- Install requirements ---
echo -e "${CYAN}[2/3] Installing dependencies from requirements.txt...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}      Error: requirements.txt not found in current directory.${NC}"
    deactivate
    exit 1
fi
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "      Dependencies installed successfully."
echo ""

# --- Create keys.json ---
echo -e "${CYAN}[3/3] Creating data/bot_config/keys.json...${NC}"
mkdir -p data/bot_config

KEYS_FILE="data/bot_config/keys.json"

if [ -f "$KEYS_FILE" ]; then
    echo -e "${YELLOW}      Warning: $KEYS_FILE already exists. Skipping creation to avoid overwriting.${NC}"
else
    cat > "$KEYS_FILE" <<EOF
{
    "bot_token": "YOUR_BOT_TOKEN",
    "gemini_api_key": "YOUR_GEMINI_API_KEY"
}
EOF
    echo -e "      Created ${CYAN}$KEYS_FILE${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}  !! ACTION REQUIRED !!${NC}"
echo -e "${YELLOW}  Open ${CYAN}$KEYS_FILE${YELLOW} and replace the placeholder values:${NC}"
echo ""
echo -e "    ${CYAN}\"bot_token\"${NC}      — your Telegram bot token"
echo -e "    ${CYAN}\"gemini_api_key\"${NC} — your Google Gemini API key"
echo ""
echo -e "${YELLOW}  Do NOT commit this file to version control.${NC}"
echo -e "${YELLOW}  By default, ${CYAN}data/${YELLOW} added to .gitignore.${NC}"
echo ""
echo -e "  To activate the virtual environment later, run:"
echo -e "    ${CYAN}source .venv/bin/activate${NC}"
echo ""