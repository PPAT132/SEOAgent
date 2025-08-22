#!/bin/bash

# Quick test script for optimize_v2 endpoint using curl
# Usage: ./quick_test_optimize_v2.sh

BASE_URL="http://localhost:8000"
ENDPOINT="/optimize_v2"

echo "🧪 Quick Test for optimize_v2 Endpoint"
echo "=================================="
echo "🎯 URL: ${BASE_URL}${ENDPOINT}"
echo ""

# Check if server is running
echo "🔌 Checking server connection..."
if curl -s "${BASE_URL}/test" > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server is not accessible"
    echo "💡 Start server with: cd backend && uvicorn app.main:app --reload"
    exit 1
fi

# Sample HTML for testing
HTML_CONTENT='<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title></title>
    <meta name="description" content="">
</head>
<body>
    <h1>Test Page</h1>
    <p>This page needs SEO optimization.</p>
    <img src="https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=300" alt="">
    <img src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400">
</body>
</html>'

echo ""
echo "📄 Sending HTML content ($(echo "$HTML_CONTENT" | wc -c) characters)..."
echo "⏳ Processing request..."

# Send POST request
RESPONSE=$(curl -s -X POST "${BASE_URL}${ENDPOINT}" \
    -H "Content-Type: application/json" \
    -d "{\"html\": \"$(echo "$HTML_CONTENT" | sed 's/"/\\"/g' | tr '\n' ' ')\"}" \
    -w "\nHTTP_STATUS:%{http_code}")

# Extract HTTP status
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1 | cut -d: -f2)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo "📊 HTTP Status: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Request successful!"
    echo ""
    
    # Parse and display key information
    echo "📋 Response Summary:"
    echo "==================="
    
    # Check if response contains success field
    SUCCESS=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', 'unknown'))" 2>/dev/null)
    
    if [ "$SUCCESS" = "True" ]; then
        echo "✅ Optimization Status: SUCCESS"
        
        # Extract key metrics
        ORIGINAL_SCORE=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('original_seo_score', 'N/A'))" 2>/dev/null)
        OPTIMIZED_SCORE=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('optimized_seo_score', 'N/A'))" 2>/dev/null)
        ISSUES_COUNT=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('issues_processed', 'N/A'))" 2>/dev/null)
        
        echo "🔢 Original SEO Score: $ORIGINAL_SCORE"
        echo "🔢 Optimized SEO Score: $OPTIMIZED_SCORE"
        echo "🔧 Issues Processed: $ISSUES_COUNT"
        
        # Save response to file
        echo "$RESPONSE_BODY" | python3 -m json.tool > optimize_v2_quick_test.json 2>/dev/null
        echo ""
        echo "💾 Full response saved to: optimize_v2_quick_test.json"
        
    elif [ "$SUCCESS" = "False" ]; then
        echo "❌ Optimization Status: FAILED"
        ERROR=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'Unknown error'))" 2>/dev/null)
        echo "🚨 Error: $ERROR"
    else
        echo "⚠️ Unexpected response format"
        echo "Raw response:"
        echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
    fi
    
else
    echo "❌ Request failed with HTTP $HTTP_STATUS"
    echo "Response:"
    echo "$RESPONSE_BODY"
fi

echo ""
echo "🏁 Quick test completed"
