#!/bin/bash
# MemoryStack Installation Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "┌─────────────────────────────────────────┐"
echo "│         MemoryStack Installer           │"
echo "│   77% token reduction. Perfect memory.  │"
echo "└─────────────────────────────────────────┘"
echo -e "${NC}"

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check Redis
echo -e "${BLUE}Checking Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis is installed but not running${NC}"
        echo -e "${YELLOW}   Start it with: redis-server${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis not found. You'll need to install it:${NC}"
    echo -e "${YELLOW}   macOS: brew install redis${NC}"
    echo -e "${YELLOW}   Ubuntu/Debian: sudo apt-get install redis-server${NC}"
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env configuration file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys:${NC}"
    echo -e "${YELLOW}   1. OPENAI_API_KEY (required for Tier 2)${NC}"
    echo -e "${YELLOW}   2. NEO4J credentials (if using Graphiti)${NC}"
    echo -e "${YELLOW}   3. SUPERMEMORY_API_KEY (if using Supermemory)${NC}"
    echo ""
    echo -e "${BLUE}Edit now? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create profiles directory
mkdir -p profiles
echo -e "${GREEN}✓ Profiles directory created${NC}"

# Success message
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo -e "  1. ${YELLOW}Configure .env file:${NC}"
echo -e "     nano .env"
echo ""
echo -e "  2. ${YELLOW}Start Redis (if not running):${NC}"
echo -e "     redis-server"
echo ""
echo -e "  3. ${YELLOW}Start MemoryStack:${NC}"
echo -e "     source venv/bin/activate"
echo -e "     python -m uvicorn src.contextflow.main:app --host 0.0.0.0 --port 8000"
echo ""
echo -e "  4. ${YELLOW}Or use the start script:${NC}"
echo -e "     ./scripts/start.sh"
echo ""
echo -e "  5. ${YELLOW}Test it:${NC}"
echo -e "     curl http://localhost:8000/health"
echo ""
echo -e "${BLUE}Documentation:${NC} docs/"
echo -e "${BLUE}Examples:${NC} examples/"
echo -e "${BLUE}Help:${NC} https://github.com/joaolvivas/contextflow"
echo ""
echo -e "${GREEN}Happy memory stacking! 🧠💚${NC}"
