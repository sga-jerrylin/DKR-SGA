#!/bin/bash
set -e

echo "🚀 DKR Backend Starting..."

# Create necessary directories if they don't exist
echo "📁 Creating data directories..."
mkdir -p /app/data/documents
mkdir -p /app/data/videos
mkdir -p /app/data/summaries
mkdir -p /app/data/indexes
mkdir -p /app/data/temp
mkdir -p /app/data/cache
mkdir -p /app/logs

# Check if library_index.json exists, create if not
if [ ! -f "/app/data/library_index.json" ]; then
    echo "📚 Creating library index..."
    cat > /app/data/library_index.json << EOF
{
  "version": "1.0",
  "categories": {},
  "total_documents": 0,
  "created_at": null,
  "updated_at": null
}
EOF
fi

# Validate critical environment variables
echo "🔍 Validating environment variables..."
if [ -z "$DEEPSEEK_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  WARNING: No API keys found. Some features may not work."
fi

if [ -z "$OCR_API_URL" ]; then
    echo "⚠️  WARNING: OCR_API_URL not set. Using default: http://111.230.37.43:5010"
    export OCR_API_URL="http://111.230.37.43:5010"
fi

echo "✅ Environment validation complete"
echo "🎯 Starting application..."

# Execute the main command
exec "$@"

