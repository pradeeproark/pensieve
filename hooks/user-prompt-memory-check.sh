#!/bin/bash
# UserPromptSubmit hook - Reminds Claude to check memories after user asks questions
# This hook fires after the user submits a prompt

echo "🔍 Context Check: Consider using memory-management skill to search for relevant memories before responding"
echo "   Search command: pensieve entry search"
exit 0
