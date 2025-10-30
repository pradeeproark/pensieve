#!/bin/bash
# SessionEnd hook - Reminds Claude to record memories before session ends
# This hook fires when a session is closing
# Encourages capturing end-of-session insights before context is lost

echo "💾 Session End: Consider using memory-management skill to record any significant learnings from this session before closing"
exit 0
