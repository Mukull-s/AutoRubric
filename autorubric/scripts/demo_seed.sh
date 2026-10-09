#!/bin/bash
# Uploads demo data to local AutoRubric instance via API.

API_URL="http://localhost:8000"

# Get token
TOKEN=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin" | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')

if [ -z "$TOKEN" ]; then
    echo "Failed to get auth token. Is the backend running on port 8000?"
    exit 1
fi

echo "Uploading Rubric..."
curl -s -X POST $API_URL/rubrics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @demo/rubric.json

echo "Uploading PDFs..."
# Since submission endpoints might expect multipart form data:
for f in demo/*.pdf; do
    echo "Uploading $f..."
    curl -s -X POST $API_URL/submissions \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@$f" \
      -F "rubric_id=demo_rubric"
done

echo "Demo seed complete."
