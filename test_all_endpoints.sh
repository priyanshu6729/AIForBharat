#!/bin/bash

BASE_URL="https://codexa-backend.up.railway.app"

echo "🧪 Testing All Codexa API Endpoints"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test health endpoints
echo "${YELLOW}📊 Health Endpoints${NC}"
echo "1. Basic Health Check"
curl -s "$BASE_URL/health" | jq '.'

echo ""
echo "2. Detailed Health Check"
curl -s "$BASE_URL/health/detailed" | jq '.'

# Test authentication
echo ""
echo "${YELLOW}🔐 Authentication Endpoints${NC}"
echo "3. Register User"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-'$(date +%s)'@example.com",
    "password": "SecurePass123!"
  }')
echo "$REGISTER_RESPONSE" | jq '.'

echo ""
echo "4. Login User"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com",
    "password": "SecurePass123!"
  }')
echo "$LOGIN_RESPONSE" | jq '.'

# Extract token (if login successful)
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -n "$TOKEN" ]; then
  echo "${GREEN}✓ Token obtained${NC}"
  
  echo ""
  echo "5. Get Current User"
  curl -s "$BASE_URL/api/auth/me" \
    -H "Authorization: Bearer $TOKEN" | jq '.'
  
  # Test analysis
  echo ""
  echo "${YELLOW}📊 Analysis Endpoints${NC}"
  echo "6. Analyze Code"
  ANALYSIS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/analyze" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "code": "def hello():\n    print(\"Hello, World!\")",
      "language": "python",
      "teaching_mode": "explanation"
    }')
  echo "$ANALYSIS_RESPONSE" | jq '.'
  
  ANALYSIS_ID=$(echo "$ANALYSIS_RESPONSE" | jq -r '.id // empty')
  
  if [ -n "$ANALYSIS_ID" ]; then
    echo ""
    echo "7. Get Analysis by ID"
    curl -s "$BASE_URL/api/analyze/$ANALYSIS_ID" \
      -H "Authorization: Bearer $TOKEN" | jq '.'
  fi
  
  echo ""
  echo "8. Get Analysis History"
  curl -s "$BASE_URL/api/analyze/history" \
    -H "Authorization: Bearer $TOKEN" | jq '.'
  
  # Test visualization
  echo ""
  echo "${YELLOW}🎨 Visualization Endpoints${NC}"
  echo "9. Create Visualization"
  curl -s -X POST "$BASE_URL/api/visualize" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "code": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
      "language": "python",
      "visualization_type": "ast"
    }' | jq '.'
  
  # Test guidance
  echo ""
  echo "${YELLOW}💡 Guidance Endpoints${NC}"
  echo "10. Get AI Guidance"
  curl -s -X POST "$BASE_URL/api/guidance" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "code": "for i in range(10): print(i)",
      "language": "python",
      "question": "How can I optimize this?"
    }' | jq '.'
  
  # Test sessions
  echo ""
  echo "${YELLOW}🔄 Session Endpoints${NC}"
  echo "11. Create Session"
  SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/session" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Test Session",
      "language": "python"
    }')
  echo "$SESSION_RESPONSE" | jq '.'
  
  echo ""
  echo "12. List Sessions"
  curl -s "$BASE_URL/api/session" \
    -H "Authorization: Bearer $TOKEN" | jq '.'
  
else
  echo "${RED}✗ No token - skipping protected endpoints${NC}"
fi

echo ""
echo "===================================="
echo "${GREEN}✓ Test Complete!${NC}"
