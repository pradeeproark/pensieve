---
name: memory-management
description: Use when starting work on a project, solving complex problems, or discovering patterns - guides effective use of Pensieve memory system for curated project knowledge. ALSO use when user says keywords like "memory", "recall", "remember", "note that", "note this", "past", "record this", "save this", "don't forget", or asks about previous sessions/learnings
---

<EXTREMELY-IMPORTANT>
This skill guides you to use Pensieve as a **curated notebook**, not a comprehensive log.

**Key Principle**: Record insights that will save time later, not every action you take.

**When to use this skill:**
- Starting work on a new or existing project
- After solving a complex, non-obvious problem
- After discovering a useful pattern in the codebase
- After learning a workaround for a tool/library issue
- After finding key documentation or resources
- When stuck on a problem (to retrieve past learnings)
</EXTREMELY-IMPORTANT>

# MANDATORY TODO PROTOCOL

<CRITICAL>
**BEFORE starting any work that uses TodoWrite, you MUST add these two todos to your todo list:**

1. **FIRST TODO** (at the start of your list):
   ```
   content: "Search Pensieve for relevant memories related to this task"
   activeForm: "Searching Pensieve for relevant memories"
   status: "pending"
   ```

2. **LAST TODO** (at the end of your list):
   ```
   content: "Evaluate and record learnings to Pensieve if valuable"
   activeForm: "Evaluating and recording learnings to Pensieve"
   status: "pending"
   ```

**This is NOT optional. This is NOT a suggestion. You MUST include both todos.**

**Why this matters:**
- The first todo ensures you don't duplicate work or miss existing solutions
- The last todo ensures valuable learnings don't get lost
- Pensieve is worthless if memories aren't retrieved and recorded consistently

**Exceptions:**
- Trivial single-step tasks (like "read this file" or "explain this code") don't need todos at all
- If you're not using TodoWrite for a task, these todos aren't required
- But if you ARE using TodoWrite, these todos are MANDATORY
</CRITICAL>

# MANDATORY SESSION START PROTOCOL

<CRITICAL>
**BEFORE responding to ANY user request in a project, you MUST complete this checklist:**

1. ☐ Invoke the `memory-management` skill using the Skill tool
2. ☐ Run `pensieve entry search` to check for existing memories
3. ☐ Show the search output to the user (even if empty)
4. ☐ Acknowledge what was found or explicitly state "No memories found"

**This is NOT optional. This is NOT a suggestion. You MUST complete this protocol.**

**Why this matters:**
- Without searching, you may duplicate work already done
- Past learnings contain solutions to problems you're about to face
- Empty searches are OK - acknowledging them shows you checked
- Skipping this protocol means wasting time re-discovering solutions

**Note**: Saying "No memories found" is REQUIRED. It proves you checked.
</CRITICAL>

# COMMON RATIONALIZATIONS (THAT MEAN YOU'RE ABOUT TO FAIL)

<CRITICAL>
**If you catch yourself thinking ANY of these thoughts, STOP. You are rationalizing your way into failure.**

## Rationalizations About Searching

1. **"I already searched at the start of the session"**
   - **WRONG**: Context changes. Search again when starting new tasks or hitting blockers.
   - **Why**: New keywords or problem areas may surface different memories.

2. **"This is too small to need a memory search"**
   - **WRONG**: Small tasks often connect to larger patterns. Search anyway.
   - **Why**: A "simple" bug might be a known gotcha with a recorded solution.

3. **"No results means nothing relevant exists"**
   - **WRONG**: You must acknowledge the empty search explicitly.
   - **Why**: Silence makes it look like you never searched. Say "No memories found."

4. **"I can search while working on the solution"**
   - **WRONG**: Search BEFORE starting work, not during.
   - **Why**: You might waste time on an approach that's already known to fail.

5. **"Let me gather information first, then search"**
   - **WRONG**: Pensieve IS information. Search first.
   - **Why**: Past learnings tell you WHAT to gather and WHERE to look.

## Rationalizations About Recording

6. **"This is too small/simple to record"**
   - **WRONG**: Use the 3-question rubric to decide, not intuition.
   - **Why**: What seems simple now is often hard-won knowledge. Apply the rubric honestly.

7. **"It's probably documented somewhere else"**
   - **WRONG**: Check rubric question #2 properly. Is it ACTUALLY documented?
   - **Why**: "Probably documented" usually means "I'm too lazy to record it."

8. **"I'll remember this for next time"**
   - **WRONG**: You won't. Agents don't retain memory between sessions.
   - **Why**: This is literally why Pensieve exists. Record it now.

9. **"I'm too busy to record right now"**
   - **WRONG**: Spawn a subagent. Main work continues immediately.
   - **Why**: Recording is async and non-blocking. No excuse.

10. **"Let me finish everything first, then record"**
    - **WRONG**: Record immediately while details are fresh.
    - **Why**: Memory fades fast. Critical details will be lost by end of session.

11. **"The user didn't ask me to record this"**
    - **WRONG**: Recording valuable learnings is YOUR responsibility, not the user's.
    - **Why**: Pensieve is for future agents (including future-you). Don't leave gaps.

## Rationalizations About the Rubric

12. **"I don't need to write out the rubric evaluation"**
    - **WRONG**: Rubric evaluation MUST be visible and explicit.
    - **Why**: Silent evaluation means no evaluation. Make it visible or you're skipping it.

13. **"This obviously doesn't meet the threshold"**
    - **WRONG**: If it's obvious, showing the rubric score takes 10 seconds. Do it anyway.
    - **Why**: "Obviously skip" often means "I didn't think about it carefully."

**Why These Rationalizations Are Dangerous:**

Every one of these thoughts leads to the same failure mode: **valuable knowledge gets lost**.

- Skip searching → waste time rediscovering solutions
- Skip recording → next agent wastes time you just saved
- Skip rubric → record too little (miss insights) or too much (noise)

**The Fix:**

When you catch yourself rationalizing, STOP and follow the mandatory protocols:
- Searching? Show output or acknowledge "No memories found"
- Recording? Apply visible rubric evaluation, spawn subagent if 3/3
- Unsure? Better to err on the side of recording. Future-you will thank you.
</CRITICAL>

# Pensieve Memory Management for Agents

## Philosophy: Notebook, Not Logger

Pensieve is your curated project notebook. It should contain **high-signal memories** that help you (or other agents) work more effectively on this project.

**Think of Pensieve like a physical notebook where you:**
- ✅ Sketch out complex problem solutions
- ✅ Note down "aha!" moments and patterns
- ✅ Write reminders about gotchas
- ✅ Keep important URLs and references

**NOT like a comprehensive log where you:**
- ❌ Record every command executed
- ❌ Document routine tasks
- ❌ Duplicate information from READMEs
- ❌ Keep temporary debugging notes

**The Test**: Ask yourself: "If I come back to this project in 3 months, will this memory save me time?"

## Discovering Pensieve Capabilities

Pensieve is designed to be self-documenting. Use these commands to discover its features:

```bash
# See all available commands
pensieve --help

# List existing templates
pensieve template list

# See template structure
pensieve template show <template-name>

# Search for entries
pensieve entry search --help

# See entry details
pensieve entry show <entry-id>
```

**Key capabilities** (run `pensieve --help` for details):
- Template management (create, list, show)
- Entry management (create, list, show, search)
- Memory linking and status tracking
- Tag-based organization
- Project auto-detection from git repos

## Part 1: Recording Memories - When and What

### When to Record

Record a memory when you've learned something **non-obvious** that:
1. Took significant time to figure out (>30 minutes)
2. Isn't documented elsewhere (not in README, comments, or easily Googled)
3. Will likely come up again (helps future-you or others in 3+ months)

### The 3-Question Decision Rubric

<CRITICAL>
**You MUST output your rubric evaluation visibly. Silent evaluation = no evaluation.**

**Required format when deciding whether to record:**

```
## Pensieve Recording Decision

**What I just completed:** [1-2 sentence summary]

**Rubric Evaluation:**
1. Complexity (>30 min, non-obvious solution): YES/NO
   - Reasoning: [Why yes or no]

2. Novelty (not documented elsewhere): YES/NO
   - Reasoning: [Why yes or no]

3. Reusability (helps in 3+ months): YES/NO
   - Reasoning: [Why yes or no]

**Score: X/3**
**Decision: RECORD / BORDERLINE / SKIP**

[If RECORD: "Spawning subagent to record..."]
[If BORDERLINE: "Asking user for decision..."]
[If SKIP: "Skipping - below threshold"]
```

**Scoring Guide:**
- **3 Yes answers** → Definitely record (spawn subagent immediately)
- **2 Yes answers** → Borderline case (ask user with AskUserQuestion)
- **0-1 Yes answers** → Skip recording (too routine)

**This format is MANDATORY when:**
- You just completed a complex task
- You're deciding whether to record something
- You're about to skip recording something

**Exception:** Only skip the visible evaluation for obviously-routine tasks (like fixing typos, adding imports). If you're even slightly unsure, SHOW THE RUBRIC.
</CRITICAL>

### What Makes a Good Memory

**Good memories include:**
- **The problem**: Clear description of what was wrong
- **The root cause**: WHY it happened (not just what)
- **The solution**: HOW it was fixed (with file:line references)
- **The learning**: Key takeaway for future situations
- **Context**: When/why this matters

**Bad memories (don't record these):**
- Routine fixes ("added missing import")
- Already documented information ("how to run tests")
- Temporary debugging notes
- No context or explanation

## Part 2: Non-Disruptive Recording with Subagents

**IMPORTANT**: When you're in the middle of work and identify something worth recording, DON'T stop what you're doing. Use a subagent to record asynchronously.

### Workflow

1. **Apply the 3-question rubric** (output it visibly)
2. **If score is 3/3**: Spawn a memory-recording subagent
3. **Continue your main work immediately** - don't wait for the subagent
4. **When subagent reports back**, acknowledge briefly but don't context-switch

**Why this works:** The subagent handles all Pensieve interaction independently. You stay focused on the main task. The recording happens in parallel, not serially.

### Subagent Prompt Template

Use this template when spawning memory-recording subagents:

```python
Task(
  subagent_type="general-purpose",
  description="Record solution to Pensieve",
  prompt="""
  Record a memory to Pensieve based on this context:

  **What happened:**
  [Brief description of problem/pattern/workaround/resource]

  **Key details:**
  - [Detail 1]
  - [Detail 2]
  - [Detail 3]

  **Your task:**
  1. Determine the most appropriate template using: pensieve template list
  2. Review the template structure: pensieve template show <name>
  3. Create the entry with all relevant fields
  4. Verify the entry was created successfully
  5. Report back with the entry ID

  Do NOT do anything else. Just record this memory and confirm.
  """
)
```

**Adapt the context section** to include:
- For problems: problem, root cause, solution, files changed, learning
- For patterns: name, description, location, why useful, example
- For workarounds: issue, workaround, why needed, reference
- For resources: name, URL, what it covers, when useful

## Part 3: Retrieving Memories

### EVIDENCE BEFORE CLAIMS

<CRITICAL>
**You MUST show actual search output before claiming you searched. Evidence before assertions, always.**

**The Rule:**
- CANNOT say: "I checked Pensieve"
- CANNOT say: "I searched for memories"
- CANNOT say: "No relevant memories found"
- MUST show: Actual command and actual output

**Required Evidence Format:**

```
Let me search Pensieve for relevant memories.

[Runs: pensieve entry search]

Output:
Entry #42 (2024-10-15): "OAuth2 token validation timing issues"
Entry #67 (2024-10-20): "CI clock drift causing auth failures"

Found 2 relevant entries. Let me review...
```

OR (for empty searches):

```
[Runs: pensieve entry search]

Output: No entries found

No existing memories. This is new ground.
```

**Why This Matters:**

1. **Proves you actually searched** - Words are cheap, output is evidence
2. **Shows what you found** - Makes discoveries visible and usable
3. **Demonstrates empty searches** - "No results" is different from "didn't search"
4. **Enables verification** - User/reviewer can confirm you checked properly
5. **Prevents lying** - Easy to say "I searched" without actually doing it

No evidence = didn't happen.
</CRITICAL>

### When to Search

**At session start:**
```bash
# See recent memories for context
pensieve entry search
```

**Before starting similar tasks:**
```bash
# Search by template type
pensieve entry search --template <name>

# Search by keywords (use --help to see search options)
pensieve entry search --help
```

**When stuck:**
Check for existing solutions or workarounds before investigating from scratch.

**Spend 2-3 minutes reading:** This refreshes context and prevents re-discovering solutions.

## Part 4: Memory Maintenance

### Keeping Memories Fresh

**When better solutions found:**
- DON'T delete old entry
- DO create new entry linking to the old one
- Explain why the new approach is better

**When workarounds become obsolete:**
- Create entry marking it as resolved/deprecated
- Reference the old entry
- Explain what changed

### Quality Checklist

Before recording, verify:
- [ ] **Specific**: Contains concrete details, not vague descriptions
- [ ] **Actionable**: Someone can use this information immediately
- [ ] **Contextualized**: Explains "why" not just "what"
- [ ] **Future-proof**: Will make sense 6 months from now
- [ ] **Non-obvious**: Not something easily Googled or in docs

## Part 5: Anti-Patterns - What NOT to Do

### DON'T Record Everything

**❌ WRONG:**
```
Entry 1: "Ran formatter"
Entry 2: "Fixed typo in comment"
Entry 3: "Updated variable name"
```

These are routine actions, not insights.

**✅ RIGHT:**
```
Entry: "Discovered project uses specific formatter config that
enforces 100-char line length via pre-commit hook.
Configuration in pyproject.toml:25-30."
```

This is useful context about project conventions.

### DON'T Copy-Paste Large Blocks

**❌ WRONG:**
```
solution: "Changed authentication.py to:
[400 lines of code pasted here]"
```

**✅ RIGHT:**
```
solution: "Modified token validation to add 120s tolerance window.
See src/auth/validator.py:234-240. Key change is timedelta comparison
with abs() to handle clock skew in either direction."
```

### DON'T Skip the "Why"

**❌ WRONG:**
```
problem: "Tests failing"
solution: "Fixed tests"
```

**✅ RIGHT:**
```
problem: "Tests failing with 'fixture not found' error"
root_cause: "conftest.py was not in test directory root. Pytest
requires conftest.py at the test root level to make fixtures available."
solution: "Moved conftest.py from tests/unit/ to tests/"
learned: "Pytest fixture discovery is directory-based. Always check
conftest.py location when fixtures aren't found."
```

### DON'T Wait Too Long

**Record immediately after learning.** Memory fades fast, and details matter.

- ✅ Record within 5 minutes of solving/discovering
- ❌ Wait until end of session (you'll forget key details)

## Summary: The 3 Rules of Pensieve

1. **Quality Over Quantity**: Record insights, not actions
2. **Context Is King**: Always include the "why"
3. **Future-Focused**: Ask "Will this save time later?"

**Remember**: A well-maintained Pensieve with 10 high-quality entries is more valuable than 100 low-signal entries.

Use this skill consistently, and Pensieve will become your most valuable project resource.
