#!/bin/bash

# Smart CCTV Backend Validation Script
# This script validates that the backend is properly set up and running

BASE_URL="http://localhost:5000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Smart CCTV Backend Validation"
echo "=========================================="
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. JSON responses will not be formatted.${NC}"
    echo "Install with: brew install jq (macOS) or sudo apt-get install jq (Linux)"
    JQ_CMD="cat"
else
    JQ_CMD="jq ."
fi

# Test 1: Health Check
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" $BASE_URL/api/health)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)

if [ "$HEALTH_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$HEALTH_BODY" | $JQ_CMD
else
    echo -e "${RED}✗ Health check failed (HTTP $HEALTH_CODE)${NC}"
    echo "$HEALTH_BODY"
    echo ""
    echo "Make sure the backend server is running: python run.py"
    exit 1
fi

echo ""

# Test 2: Register User
echo "2. Registering test user..."
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!"
  }')
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)
REGISTER_CODE=$(echo "$REGISTER_RESPONSE" | tail -n 1)

if [ "$REGISTER_CODE" == "201" ] || [ "$REGISTER_CODE" == "200" ]; then
    echo -e "${GREEN}✓ User registration successful${NC}"
    echo "$REGISTER_BODY" | $JQ_CMD
elif [ "$REGISTER_CODE" == "400" ]; then
    echo -e "${YELLOW}⚠ User may already exist (HTTP $REGISTER_CODE)${NC}"
    echo "$REGISTER_BODY" | $JQ_CMD
else
    echo -e "${RED}✗ User registration failed (HTTP $REGISTER_CODE)${NC}"
    echo "$REGISTER_BODY" | $JQ_CMD
    exit 1
fi

echo ""

# Test 3: Login
echo "3. Testing login..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }')
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)
LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)

if [ "$LOGIN_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    TOKEN=$(echo "$LOGIN_BODY" | $JQ_CMD -r '.access_token // empty')
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}✗ No access token in response${NC}"
        echo "$LOGIN_BODY" | $JQ_CMD
        exit 1
    else
        echo "Token received: ${TOKEN:0:50}..."
    fi
else
    echo -e "${RED}✗ Login failed (HTTP $LOGIN_CODE)${NC}"
    echo "$LOGIN_BODY" | $JQ_CMD
    exit 1
fi

echo ""

# Test 4: Protected Endpoint
echo "4. Testing protected endpoint (GET /api/auth/me)..."
ME_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BASE_URL/api/auth/me \
  -H "Authorization: Bearer $TOKEN")
ME_BODY=$(echo "$ME_RESPONSE" | head -n -1)
ME_CODE=$(echo "$ME_RESPONSE" | tail -n 1)

if [ "$ME_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Protected endpoint access successful${NC}"
    echo "$ME_BODY" | $JQ_CMD
else
    echo -e "${RED}✗ Protected endpoint access failed (HTTP $ME_CODE)${NC}"
    echo "$ME_BODY" | $JQ_CMD
    exit 1
fi

echo ""

# Test 5: Create Camera
echo "5. Testing camera creation..."
CAMERA_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/api/cameras \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Camera",
    "location": "Test Location",
    "status": "active"
  }')
CAMERA_BODY=$(echo "$CAMERA_RESPONSE" | head -n -1)
CAMERA_CODE=$(echo "$CAMERA_RESPONSE" | tail -n 1)

if [ "$CAMERA_CODE" == "201" ] || [ "$CAMERA_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Camera creation successful${NC}"
    echo "$CAMERA_BODY" | $JQ_CMD
    CAMERA_ID=$(echo "$CAMERA_BODY" | $JQ_CMD -r '.id // empty')
else
    echo -e "${RED}✗ Camera creation failed (HTTP $CAMERA_CODE)${NC}"
    echo "$CAMERA_BODY" | $JQ_CMD
    exit 1
fi

echo ""

# Test 6: List Cameras
echo "6. Testing camera listing..."
LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BASE_URL/api/cameras \
  -H "Authorization: Bearer $TOKEN")
LIST_BODY=$(echo "$LIST_RESPONSE" | head -n -1)
LIST_CODE=$(echo "$LIST_RESPONSE" | tail -n 1)

if [ "$LIST_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Camera listing successful${NC}"
    echo "$LIST_BODY" | $JQ_CMD
else
    echo -e "${RED}✗ Camera listing failed (HTTP $LIST_CODE)${NC}"
    echo "$LIST_BODY" | $JQ_CMD
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All validation tests passed!${NC}"
echo "=========================================="
echo ""
echo "Backend is properly configured and running."
echo "You can now proceed with frontend development or API testing."

