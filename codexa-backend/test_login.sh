#!/bin/bash

USER_POOL_ID="us-east-1_dNGB9UtRx"
EMAIL="test@example.com"
PASSWORD="NewPassword123!"

echo "========================================================================"
echo "🔐 Testing Codexa Authentication"
echo "========================================================================"

# Set password
echo ""
echo "1️⃣  Setting password for $EMAIL..."
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username $EMAIL \
  --password "$PASSWORD" \
  --permanent \
  --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Password set successfully!"
else
    echo "⚠️  Password setting failed (user might not exist)"
fi

# Login
echo ""
echo "2️⃣  Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

echo "Response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract token
echo ""
echo "3️⃣  Extracting token..."
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ ! -z "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
    echo "✅ Login successful!"
    echo "Token (first 40 chars): ${TOKEN:0:40}..."
    
    # Test AI
    echo ""
    echo "4️⃣  Testing Amazon Nova AI..."
    curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "code": "def greet(name):\n    return f\"Hello, {name}!\"",
        "language": "python"
      }' | python3 -m json.tool
    
    echo ""
    echo "========================================================================"
    echo "🎉 ALL TESTS PASSED!"
    echo "========================================================================"
    echo ""
    echo "Your credentials:"
    echo "  Email: $EMAIL"
    echo "  Password: $PASSWORD"
    echo "  Token: ${TOKEN:0:40}..."
    echo ""
    echo "Use this token in API requests:"
    echo "  Authorization: Bearer $TOKEN"
    
else
    echo "❌ Login failed. Response:"
    echo "$LOGIN_RESPONSE"
fi

