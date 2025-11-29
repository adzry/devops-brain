#!/bin/bash
# Start Frontend with Auto-Open Browser

set -e

echo "🚀 Starting DevOps Brain Frontend..."
echo ""

cd "$(dirname "$0")/../frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start Next.js dev server
echo "🌐 Starting Next.js dev server on http://localhost:3000"
echo "📱 Frontend will auto-open in browser..."
echo ""

# Start dev server and open browser
if command -v open &> /dev/null; then
    # macOS
    (sleep 3 && open http://localhost:3000) &
elif command -v xdg-open &> /dev/null; then
    # Linux
    (sleep 3 && xdg-open http://localhost:3000) &
elif command -v start &> /dev/null; then
    # Windows
    (sleep 3 && start http://localhost:3000) &
fi

npm run dev
