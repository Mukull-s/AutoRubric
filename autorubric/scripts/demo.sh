#!/bin/bash
set -e

echo "Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin" | jq -r .access_token)

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
for i in {1..10}; do
  STATUS=$(curl -s -X GET http://localhost:8000/jobs/$JOB_ID \
    -H "Authorization: Bearer $TOKEN" | jq -r .status)
  echo "Status: $STATUS"
  if [ "$STATUS" = "DONE" ]; then
    break
  fi
  sleep 2
done

echo "Getting result..."
curl -s -X GET http://localhost:8000/results/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
