#!/usr/bin/env bash

WEBHOOK_URL="https://hooks.slack.com/services/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"

MESSAGE=$(/usr/local/bin/python3 /Users/moltea/.openclaw/workspace/v1/main.py)

# payload=$(jq -n --arg text "$MESSAGE" '{text: $text}')

payload=$(python3 -c 'import json,sys; print(json.dumps({"text": sys.stdin.read()}))' <<< "$MESSAGE")


send_slack() {
  local text="$1"

  curl -s -w "\n%{http_code}" -X POST \
    -H "Content-type: application/json" \
    --data "$payload" \
    "$WEBHOOK_URL"
}

# Send the original message
response=$(send_slack "$MESSAGE")

body=$(echo "$response" | head -n1)
status=$(echo "$response" | tail -n1)

# Check for failure
if [[ "$status" != "200" ]]; then
  error_msg=":x: Slack message failed
	Status: $status
	Response: $body
	Original message: $MESSAGE"

  echo "Error sending message to Slack: $body (HTTP $status)"

  # Send error message to Slack
  send_slack "$error_msg" #>/dev/null

  exit 1
else
  echo "Message sent successfully"
fi



# #!/bin/bash

# # Define your Slack Webhook URL
# WEBHOOK_URL="https://hooks.slack.com/services/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"

# # Read the message from stdin or an argument
# # MESSAGE="${1:-$(cat /dev/stdin)}"

# MESSAGE=$(/usr/local/bin/python3 /Users/moltea/.openclaw/workspace/v1/main.py)

# curl -X POST \
#   -H "Content-type: application/json" \
#   --data "{\"text\":\"$MESSAGE\"}" \
#   "$WEBHOOK_URL"

# #!/usr/bin/env bash
