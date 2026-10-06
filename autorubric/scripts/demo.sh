#!/bin/bash
set -e

DEMO_EMAIL="demo_${RANDOM}@example.com"
DEMO_PASS="DemoPassword123!"

echo "Registering demo user..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$DEMO_EMAIL\", \"password\": \"$DEMO_PASS\", \"full_name\": \"Demo User\"}" | jq -r .access_token)

if [[ "$TOKEN" == "null" || -z "$TOKEN" ]]; then
  echo "Failed to register, checking if token available..."
  exit 1
fi

echo "Creating rubric..."
RUBRIC_ID=$(curl -s -X POST http://localhost:8000/rubrics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @backend/tests/fixtures/rubrics/rubric.json | jq -r .id)
echo "Rubric ID: $RUBRIC_ID"

echo "Submitting PDF..."
JOB_ID=$(curl -s -X POST http://localhost:8000/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -F "rubric_id=$RUBRIC_ID" \
  -F "file=@backend/tests/fixtures/annotation/annotated.pdf" | jq -r .job_id)
echo "Job ID: $JOB_ID"

echo "Polling job status..."
for i in {1..30}; do
  STATUS=$(curl -s -X GET http://localhost:8000/jobs/$JOB_ID \
    -H "Authorization: Bearer $TOKEN" | jq -r .status)
  echo "Status: $STATUS"
  if [[ "$STATUS" == "DONE" || "$STATUS" == "FAILED" || "$STATUS" == "NEEDS_REVIEW" ]]; then
    break
  fi
  sleep 2
done

if [[ "$STATUS" == "FAILED" ]]; then
  echo "Job failed!"
  exit 1
fi


echo "Getting result..."
curl -s -X GET http://localhost:8000/results/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
