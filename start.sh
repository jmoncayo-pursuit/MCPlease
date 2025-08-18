#!/bin/bash

echo "🚀 Starting MCPlease - One-Stop Setup..."

# Function to find available port
find_available_port() {
    local port=8000
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        echo "⚠️  Port $port is in use, trying next port..."
        port=$((port + 1))
        if [ $port -gt 8100 ]; then
            echo "❌ No available ports found between 8000-8100"
            exit 1
        fi
    done
    echo $port
}

# Find available port
PORT=$(find_available_port)
echo "🔧 Using port $PORT for HTTP server"

# Check if server is already running on this port
if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "✅ Server already running on port $PORT"
else
    echo "🔧 Starting HTTP server on port $PORT..."
    PORT=$PORT python mcplease_http_server.py &
    sleep 3
    
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "✅ Server started successfully on port $PORT"
    else
        echo "❌ Failed to start server on port $PORT"
        exit 1
    fi
fi

# Create/update VSCode workspace config
echo "⚙️  Configuring VSCode workspace..."
mkdir -p .vscode
cat > .vscode/settings.json << EOF
{
  "continue.serverUrl": "http://localhost:$PORT",
  "continue.models": [
    {
      "title": "MCPlease Local",
      "provider": "openai",
      "model": "oss-20b-local",
      "apiBase": "http://localhost:$PORT/v1",
      "apiKey": "not-needed"
    }
  ],
  "continue.defaultModel": "MCPlease Local"
}
EOF

echo "✅ VSCode configuration updated"

# Open VSCode
echo "🔌 Opening VSCode..."
code . &

echo ""
echo "🎯 MCPlease is ready!"
echo "   • Server running on port $PORT"
echo "   • Continue.dev automatically configured"
echo "   • VSCode opening with config loaded"
echo ""
echo "💡 Just press Ctrl+I in VSCode to start using MCPlease!"
echo "   No manual configuration needed!"
echo ""
echo "🎯 AI coding assistance ready with OSS-20B model!"
