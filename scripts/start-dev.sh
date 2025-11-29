#!/bin/bash
# Start Full Stack Development Environment

set -e

echo "🚀 Starting DevOps Brain Development Environment..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to open browser
open_browser() {
    sleep 5
    if command -v open &> /dev/null; then
        open http://localhost:3000
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    elif command -v start &> /dev/null; then
        start http://localhost:3000
    fi
}

# Start backend in background
echo -e "${BLUE}📡 Starting Backend API...${NC}"
cd "$(dirname "$0")/.."
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend
sleep 3

# Start frontend
echo -e "${BLUE}🎨 Starting Frontend...${NC}"
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Open browser in background
open_browser &

# Start frontend (foreground)
echo -e "${GREEN}✅ Development servers starting...${NC}"
echo -e "${GREEN}🌐 Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}🔌 Backend:  http://localhost:8000${NC}"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
