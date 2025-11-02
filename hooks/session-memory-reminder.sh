#!/bin/bash
# SessionStart hook - MANDATORY memory retrieval protocol
# This hook fires when a new session begins or resumes

cat << 'EOF'
<system-reminder>
🔴 MANDATORY SESSION START PROTOCOL

BEFORE responding to ANY user request in this project, complete this checklist:

1. ☐ Invoke memory-management skill using Skill tool
2. ☐ Run: pensieve entry search
3. ☐ Show the search output (even if empty)
4. ☐ Acknowledge findings or state "No memories found"

This is NOT optional. This is NOT a suggestion. You MUST complete this protocol.

Why: Past learnings contain solutions to problems you're about to face.
Skipping = wasting time re-discovering solutions.

Evidence before claims - show the actual search output.
</system-reminder>
EOF
exit 0
