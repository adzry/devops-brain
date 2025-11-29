#!/bin/bash
# DevOps Brain Setup Script
# Initializes the development environment

set -e

echo "🧠 DevOps Brain Setup"
echo "====================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

echo "📦 Checking Python version..."
if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
echo "🐍 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "⏭️  Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p .cache
mkdir -p data

# Set up environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << 'EOF'
# DevOps Brain Environment Configuration
# Copy this file and fill in your values

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# GitHub Integration
GITHUB_TOKEN=your_github_token_here

# Slack Integration
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_SIGNING_SECRET=your_slack_signing_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/devops_brain

# Monitoring - Datadog
DATADOG_API_KEY=your_datadog_api_key_here
DATADOG_APP_KEY=your_datadog_app_key_here

# Cloud Providers
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

GCP_PROJECT_ID=your_gcp_project_id_here
EOF
    echo "✅ .env file created - please update with your credentials"
else
    echo "⏭️  .env file already exists"
fi

# Run linting check
echo "🔍 Running lint check..."
python -m ruff check . --ignore E501 || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Update .env with your credentials"
echo "  3. Run tests: pytest"
echo ""
