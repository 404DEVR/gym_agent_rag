#!/bin/bash

# Run ingestion to build knowledge base
echo "Building knowledge base..."
python ingest.py

# Start the API server
echo "Starting API server..."
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}