#!/bin/bash

set -e  # Exit on any error

echo "Starting deployment..."

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Run ingestion to build knowledge base
echo "Building knowledge base..."
if python ingest.py; then
    echo "✅ Knowledge base built successfully"
else
    echo "⚠️ Ingestion failed, but continuing with fallback responses"
fi

# Start the API server
echo "Starting API server on port ${PORT:-8000}..."
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 30