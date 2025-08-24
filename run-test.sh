#!/bin/bash

echo "🧪 Running SEO Pipeline Test..."

# Run test in Docker container
docker exec seoagent-backend-1 python /app/tests/test_full_pipeline.py

echo "✅ Test completed!"
