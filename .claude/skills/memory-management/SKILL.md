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

**Example:**
```
User: "Help me implement user authentication"

You create todos:
[
  {
    "content": "Search Pensieve for relevant memories related to this task",
    "activeForm": "Searching Pensieve for relevant memories",
    "status": "pending"
  },
  {
    "content": "Design authentication system",
    "activeForm": "Designing authentication system",
    "status": "pending"
  },
  {
    "content": "Implement auth endpoints",
    "activeForm": "Implementing auth endpoints",
    "status": "pending"
  },
  {
    "content": "Write tests",
    "activeForm": "Writing tests",
    "status": "pending"
  },
  {
    "content": "Evaluate and record learnings to Pensieve if valuable",
    "activeForm": "Evaluating and recording learnings to Pensieve",
    "status": "pending"
  }
]
```

**When to actually perform these tasks:**
- **Pensieve search todo**: Mark in_progress when you start working, search immediately
- **Pensieve recording todo**: Mark in_progress when all work todos are completed, apply 3-question rubric

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

**Example of CORRECT behavior:**

```
User: "Help me implement user authentication"

Claude: Let me first check for existing memories about authentication in this project.

[Runs: pensieve entry search]

Found 2 relevant entries:
- Entry #42: "OAuth2 implementation with JWT tokens"
- Entry #67: "Common auth pitfall: session expiry handling"

I'll review these before proceeding...
```

**Example of INCORRECT behavior (DO NOT DO THIS):**

```
User: "Help me implement user authentication"

Claude: I'll help you implement authentication. Let's start by...

[WRONG: Skipped memory search entirely]
[WRONG: May duplicate work or miss known gotchas]
```

**Handling Empty Searches:**

```
Claude: Let me check for existing memories about authentication.

[Runs: pensieve entry search --field "problem" --value "auth" --substring]

No memories found related to authentication. This will be new ground for this project.
Now let's proceed with...
```

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

## Part 0: Setup for Project Maintainers

**If you're a project maintainer or want agents to use Pensieve on your project, follow these setup steps:**

### Step 1: Update Project CLAUDE.md

Add the following section to your project's `CLAUDE.md` (or `README.md` if you don't have a CLAUDE.md):

```markdown
## Using Pensieve Across Sessions

**IMPORTANT**: Claude agents don't retain memory between sessions. This project uses the `memory-management` skill which provides comprehensive guidance on using Pensieve effectively.

**At session start, always:**
1. Invoke the `memory-management` skill to load best practices
2. Search for existing memories: `pensieve entry search`
3. Read recent entries to restore context from previous sessions

**During work, record:**
- Complex problems solved (non-obvious bugs and their root causes)
- Patterns discovered (architectural decisions, code conventions)
- Workarounds learned (tool issues, gotchas)
- Key resources found (documentation, references)

**Quick check**: "Will this memory save time in 3 months?" If yes, record it immediately.

See the `memory-management` skill for detailed workflows, templates, and best practices.
```

### Step 2: Update Custom Agent Instructions

If you have custom agents (in `.claude/agents/` or similar), add this to their system prompts:

```markdown
# Memory Management

This project uses Pensieve for persistent memory across sessions. At the start of each session:

1. Use the `memory-management` skill
2. Search for project memories: `pensieve entry search`
3. Review relevant memories before starting work
4. Record new learnings after solving complex problems

Pensieve is your curated project notebook - record insights that will save time in the future.
```

### Step 3: Add to Project Onboarding

Include in your project's onboarding documentation or developer guide:

```markdown
## Agent Memory System

We use **Pensieve** to maintain context across development sessions. Agents should:

- Start each session by reviewing past memories
- Record non-obvious solutions to complex problems
- Document discovered patterns and gotchas
- Note key resources and documentation

This prevents re-discovering solutions and maintains project knowledge over time.

Installation: [Link to Pensieve installation instructions]
Skill: Use the `memory-management` skill for guidance
```

### Step 4: Verify Setup

After updating documentation, verify that:
- [ ] Project CLAUDE.md mentions memory-management skill
- [ ] Custom agents (if any) reference Pensieve in their instructions
- [ ] Onboarding docs explain the memory system
- [ ] Pensieve is installed: `pensieve --version`

**Why this matters**: Without these instructions, agents won't know to use Pensieve, defeating its purpose as a cross-session memory system.

---

## Part 1: Project Setup (First Time on a Project)

When you start working on a project for the first time, create project-specific memory templates.

### Step 1: Check for Existing Memories

```bash
pensieve entry search
```

If memories exist, read them to understand what past agents learned. Then skip to Part 2.

### Step 2: Create Project-Specific Templates

Create 3-5 templates based on what will be useful for THIS project. Don't create templates "just in case" - create them when you have something to record.

#### Recommended Template Types:

**1. problem_solved** - For complex bugs and technical challenges
```bash
pensieve template create

# When prompted, create fields:
# - problem (text, required, max 500): What was the issue?
# - root_cause (text, required, max 500): Why did it happen?
# - solution (text, required, max 1000): How was it fixed?
# - files_changed (text, optional): Which files were modified?
# - learned (text, required, max 500): Key takeaway
# - reference_url (url, optional): Related docs/issues
```

**2. pattern_discovered** - For useful patterns in the codebase
```bash
pensieve template create

# Fields:
# - pattern_name (text, required, max 100): Short name
# - description (text, required, max 500): What is it?
# - location (file_reference, required): Where to find it
# - why_useful (text, required, max 300): When/why to use it
# - example_code (text, optional, max 1000): Code snippet or reference
```

**3. workaround_learned** - For tool/library issues and workarounds
```bash
pensieve template create

# Fields:
# - issue (text, required, max 300): What doesn't work?
# - workaround (text, required, max 500): How to work around it
# - why_needed (text, required, max 300): Root cause if known
# - reference_url (url, optional): Issue tracker link
# - discovered_at (timestamp, required, auto_now: yes)
```

**4. key_resource** - For important documentation and references
```bash
pensieve template create

# Fields:
# - resource_name (text, required, max 100): Name/title
# - resource_url (url, required): Link
# - what_it_covers (text, required, max 300): Topics covered
# - when_useful (text, required, max 300): When to reference it
# - notes (text, optional, max 500): Additional context
```

**5. key_file** - For important files agents should know about
```bash
pensieve template create

# Fields:
# - file_path (file_reference, required): Path to file
# - purpose (text, required, max 300): What does it do?
# - gotchas (text, optional, max 500): Things to watch out for
# - related_files (text, optional): Other relevant files
# - last_updated (timestamp, required, auto_now: yes)
```

### Step 3: Create Initial Project Entry

After creating templates, record initial project knowledge:

```bash
# Use key_file template to document project structure
pensieve entry create key_file

# Example entry:
# file_path: src/main.py
# purpose: Entry point of application, initializes all services
# gotchas: Services must be initialized in specific order (see line 45-67)
# related_files: src/config.py, src/services/__init__.py
```

## Part 2: Recording Memories (During Work)

### When to Record

Record a memory when you've learned something **non-obvious** that:
1. Took significant time to figure out
2. Isn't documented elsewhere
3. Will likely come up again
4. Would help another developer

### Recording Workflow

**PAUSE after significant events:**
1. Just solved a complex bug
2. Discovered a non-obvious pattern
3. Had to work around a tool issue
4. Found documentation that unlocked understanding

**ASK: "Is this worth remembering?"**
- Will future-me benefit from this?
- Is this information findable elsewhere?
- Does it contain actionable insight?

**RECORD immediately (memory fades fast):**
```bash
pensieve entry create <template-name>
```

**INCLUDE context (the "why"):**
- Not just what you did
- WHY it works
- WHY other approaches didn't work
- WHAT you learned

### Examples of Good Memories

**Example 1: Complex Problem Solved**
```
Template: problem_solved
Project: ~/projects/myapp

problem: "Authentication tokens expiring in CI pipeline but not locally"

root_cause: "CI environment has clock drift (~90 seconds ahead). Token validation
uses strict timestamp checking without tolerance window."

solution: "Modified token validation in src/auth/validator.py:234 to add 120-second
tolerance window. This accounts for reasonable clock drift without compromising security."

files_changed: "src/auth/validator.py (line 234-240), tests/test_auth.py (new test cases)"

learned: "Always account for clock skew in distributed systems. Timestamp validation
should have tolerance windows. CI environments often have clock drift."

reference_url: "https://tools.ietf.org/html/rfc7519#section-4.1.4"
```

**Example 2: Pattern Discovered**
```
Template: pattern_discovered
Project: ~/projects/myapp

pattern_name: "Lazy service initialization"

description: "All service classes in src/services/ use a two-phase initialization:
1. __init__() creates instance with config, doesn't connect
2. .connect() method explicitly establishes connections
This pattern is used consistently across DatabaseService, CacheService, APIClient, etc."

location: "src/services/base.py"

why_useful: "Allows importing service modules without triggering connections. Makes
testing easier (can mock connect). Prevents connection errors during module import.
Follow this pattern when adding new services."

example_code: "See src/services/database.py:45-67 for canonical example. Base class
in src/services/base.py:12-30 provides the pattern."
```

**Example 3: Workaround Learned**
```
Template: workaround_learned
Project: ~/projects/myapp

issue: "pytest-cov breaks debugger (pdb/breakpoint) - breakpoints are ignored"

workaround: "Run pytest with --no-cov flag when debugging:
pytest tests/test_foo.py --no-cov -v

For VSCode launch config, add '--no-cov' to pytest args."

why_needed: "Coverage plugin uses sys.settrace() which conflicts with debugger's
use of the same hook. Can't have both active simultaneously."

reference_url: "https://github.com/pytest-dev/pytest-cov/issues/131"
```

**Example 4: Key Resource Found**
```
Template: key_resource
Project: ~/projects/myapp

resource_name: "FastAPI Best Practices Guide"

resource_url: "https://github.com/zhanymkanov/fastapi-best-practices"

what_it_covers: "Project structure, async patterns, error handling, dependency
injection, testing strategies. Highly relevant to our API structure."

when_useful: "Reference when adding new endpoints, restructuring code, or debugging
async issues. Section 7 on dependency injection is especially relevant to our auth flow."

notes: "This guide influenced our current project structure. Many patterns we use
come from here (see src/api/ organization)."
```

### Examples of BAD Memories (Don't Record These)

**❌ Too Routine:**
```
problem: "Import error"
solution: "Added missing import"
```
→ This is routine, not worth recording

**❌ No Context:**
```
problem: "Bug in authentication"
solution: "Fixed it in auth.py"
```
→ No useful information about what/why/how

**❌ Already Documented:**
```
pattern: "How to run tests"
description: "Run pytest from project root"
```
→ This should be in README, not Pensieve

**❌ Too Temporary:**
```
problem: "Debugging print statements left in code"
solution: "Removed them"
```
→ Temporary issue, not a learning

## Part 2.5: Proactive Recording (Using Hooks and Subagents)

**If you have Claude Code hooks configured** (see HOOKS_SETUP.md), you'll receive periodic reminders to check for memory-worthy moments. This section explains how to respond to those reminders efficiently.

### Trigger Moments: When Hooks Remind You

Hooks will remind you to check for recording opportunities at these key moments:

1. **Session Start**: When you begin working on a project (retrieve existing memories)
2. **After Significant Work**: When you complete responses, especially after:
   - Solving complex bugs or problems
   - Discovering architectural patterns or conventions
   - Completing major tasks or features
   - Making significant git commits

**When you see a hook reminder**, don't ignore it - but also don't let it disrupt your flow. Use the decision rubric below.

### The 3-Question Decision Rubric

When a hook reminds you to check for memory-worthy content, quickly evaluate using these three questions:

1. **Complexity**: Did this take >30 minutes to figure out, or involve a non-obvious solution?
2. **Novelty**: Is this information documented elsewhere (README, comments, obvious from code)?
3. **Reusability**: Will this help me/others in 3+ months, or on similar tasks?

**Scoring Guide:**
- **3 Yes answers** → Definitely record (spawn subagent immediately)
- **2 Yes answers** → Borderline case (ask user with AskUserQuestion)
- **0-1 Yes answers** → Skip recording (too routine)

### EXPLICIT RUBRIC OUTPUT REQUIREMENT

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

**This format is MANDATORY when:**
- A hook reminds you to check for recording
- You just completed a complex task
- You're deciding whether to record something
- You're about to skip recording something

**Why this is required:**
- Makes evaluation transparent (user/reviewer can verify)
- Prevents silent skipping (forces you to think through rubric)
- Shows your work (proves you applied rubric, not intuition)
- Catches mistakes (wrong evaluation is visible and correctable)

**Example of CORRECT visible evaluation:**

```
## Pensieve Recording Decision

**What I just completed:** Solved API timeout in production by adding nginx proxy_read_timeout and backend connection pooling.

**Rubric Evaluation:**
1. Complexity (>30 min, non-obvious solution): YES
   - Reasoning: Took 2 hours to debug. Involved tracing through nginx logs,
     application logs, and database connection metrics. Root cause was
     non-obvious interaction between connection pooling and nginx timeouts.

2. Novelty (not documented elsewhere): YES
   - Reasoning: Not in our deployment docs. Specific to our nginx + gunicorn
     + postgres setup. Checked README and deployment guide - not mentioned.

3. Reusability (helps in 3+ months): YES
   - Reasoning: Production timeout issues will happen again. This documents
     both the diagnostic process and the fix. Will save hours next time.

**Score: 3/3**
**Decision: RECORD**

Spawning subagent to record this problem solution to Pensieve while I continue with testing...
```

**Example of WRONG (silent) evaluation:**

```
[Claude thinks: "Hmm, that was complex, probably should record it... yeah I'll record it"]

I've solved the timeout issue. Now let me continue with...

[WRONG: No visible rubric evaluation]
[WRONG: Claimed to decide but showed no reasoning]
```

**Exception:** Only skip the visible evaluation for obviously-routine tasks (like fixing typos, adding imports). If you're even slightly unsure, SHOW THE RUBRIC.

</CRITICAL>

**Example Evaluation:**

```
Just solved: "API timeout in production but not staging"
- Complexity? YES (took 2 hours to debug)
- Novelty? YES (not documented, involved specific nginx config)
- Reusability? YES (will help with future deployment issues)
→ Score: 3/3 - RECORD IT via subagent
```

```
Just fixed: "Import statement missing"
- Complexity? NO (took 30 seconds)
- Novelty? NO (standard Python error)
- Reusability? NO (won't help in future)
→ Score: 0/3 - SKIP
```

### Non-Disruptive Recording with Subagents

**IMPORTANT**: When you're in the middle of work and identify something worth recording, DON'T stop what you're doing. Use a subagent to record asynchronously.

**Workflow:**

1. **Note it briefly** (1-2 sentences to the user):
   ```
   "I just solved a complex clock drift issue in CI. I'm going to spawn a
   subagent to record this to Pensieve while I continue with the next task."
   ```

2. **Spawn memory-recording subagent** (see templates below)

3. **Continue your main work immediately** - don't wait for the subagent

4. **When subagent reports back**, acknowledge briefly but don't context-switch

**Why this works:** The subagent handles all Pensieve interaction independently. You stay focused on the main task. The recording happens in parallel, not serially.

### Subagent Prompt Templates

Use these pre-written prompts when spawning memory-recording subagents:

#### Template 1: Recording a Problem Solved

```python
Task(
  subagent_type="general-purpose",
  description="Record problem solution to Pensieve",
  prompt="""
  Record a memory of a problem I just solved to Pensieve.

  **Context:**
  - Problem: [Brief description of the issue]
  - Root cause: [Why it happened]
  - Solution: [How I fixed it]
  - Files changed: [Which files were modified]
  - Key learning: [Main takeaway]

  **Your task:**
  1. Extract the key details from the context above
  2. Run: pensieve entry create problem_solved \
       --field "problem=[description]" \
       --field "root_cause=[cause]" \
       --field "solution=[fix]" \
       --field "files_changed=[files]" \
       --field "learned=[takeaway]"
  3. Verify the entry was created successfully
  4. Report back with the entry ID

  Do NOT do anything else. Just record this memory and confirm.
  """
)
```

#### Template 2: Recording a Pattern Discovered

```python
Task(
  subagent_type="general-purpose",
  description="Record discovered pattern to Pensieve",
  prompt="""
  Record a codebase pattern I just discovered to Pensieve.

  **Context:**
  - Pattern name: [Short descriptive name]
  - Description: [What the pattern is]
  - Location: [Where to find it in the code]
  - Why useful: [When/why to use this pattern]
  - Example: [Code reference or snippet]

  **Your task:**
  1. Extract pattern details from context above
  2. Run: pensieve entry create pattern_discovered \
       --field "pattern_name=[name]" \
       --field "description=[desc]" \
       --field "location=[file:line]" \
       --field "why_useful=[reason]" \
       --field "example_code=[reference]"
  3. Verify entry created successfully
  4. Report entry ID

  Just record and return. No other actions.
  """
)
```

#### Template 3: Recording a Workaround

```python
Task(
  subagent_type="general-purpose",
  description="Record workaround to Pensieve",
  prompt="""
  Record a tool/library workaround I just discovered to Pensieve.

  **Context:**
  - Issue: [What doesn't work]
  - Workaround: [How to work around it]
  - Why needed: [Root cause if known]
  - Reference: [URL to issue tracker or docs, if any]

  **Your task:**
  1. Extract workaround details from context
  2. Run: pensieve entry create workaround_learned \
       --field "issue=[problem]" \
       --field "workaround=[solution]" \
       --field "why_needed=[cause]" \
       [--field "reference_url=[url]" if available]
  3. Verify entry created
  4. Report entry ID

  Record only. No exploration or additional work.
  """
)
```

### Borderline Cases: When to Ask the User

If your rubric score is 2/3 (borderline), use AskUserQuestion to let the user decide:

```python
AskUserQuestion(
  questions=[{
    "question": "I just [completed X]. Should I record this to Pensieve?",
    "header": "Record memory?",
    "multiSelect": false,
    "options": [
      {
        "label": "Yes, record it",
        "description": "This learning is valuable and worth saving for future reference"
      },
      {
        "label": "No, skip it",
        "description": "This is routine or well-documented elsewhere"
      }
    ]
  }]
)
```

**When to use this:**
- You're unsure if the complexity threshold is met
- The information might be documented but you haven't verified
- The reusability is context-dependent

**Don't overuse:** If every recording decision goes to the user, you're not using the rubric effectively. Aim for <20% of decisions requiring user input.

### Integration with Hooks

**SessionStart Hook Workflow:**

1. Hook fires → You see reminder to retrieve memories
2. Immediately run: `pensieve entry search`
3. Read recent entries (spend 2-3 minutes)
4. Continue with user's task with refreshed context

**Stop Hook Workflow:**

1. Hook fires → You see reminder to check for recording
2. Mentally review what you just did in previous response
3. Apply 3-question rubric
4. If 3/3: Spawn subagent, continue working
5. If 2/3: Ask user with AskUserQuestion
6. If 0-1/3: Acknowledge reminder, continue without recording

**Example Response to Stop Hook:**

```
User: [asks you to implement feature X]

Claude: [implements feature, solves complex problem along the way]

[Stop hook fires: "💡 Memory Check: If you just solved..."]

Claude: "I just solved a non-obvious issue with [X] that took significant
debugging time. This meets the recording threshold (3/3 on rubric). I'm
spawning a subagent to record this to Pensieve."

[Spawns subagent with Template 1]

Claude: "Now, back to your feature implementation - let me continue with..."

[Continues main work without waiting for subagent]
```

### Quick Reference: Proactive Recording Checklist

When a hook reminds you to check for memories:

- [ ] Apply 3-question rubric (Complexity, Novelty, Reusability)
- [ ] If 3/3: Note to user, spawn subagent, continue work
- [ ] If 2/3: Ask user with AskUserQuestion
- [ ] If 0-1/3: Acknowledge and skip
- [ ] Never block main work on recording
- [ ] Use pre-written subagent templates
- [ ] Keep recording async and non-disruptive

**Remember**: The hooks are your reminder system, the rubric is your decision framework, and subagents are your execution mechanism. Together, they ensure you never miss important learnings without disrupting your workflow.

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

[Runs: pensieve entry search --template problem_solved]

Output:
Entry #42 (2024-10-15): "OAuth2 token validation timing issues"
Entry #67 (2024-10-20): "CI clock drift causing auth failures"

Found 2 relevant entries. Let me review...
```

OR (for empty searches):

```
[Runs: pensieve entry search --field "problem" --value "timeout" --substring]

Output: No entries found

No existing memories about timeouts. This is new ground.
```

**Why This Matters:**

1. **Proves you actually searched** - Words are cheap, output is evidence
2. **Shows what you found** - Makes discoveries visible and usable
3. **Demonstrates empty searches** - "No results" is different from "didn't search"
4. **Enables verification** - User/reviewer can confirm you checked properly
5. **Prevents lying** - Easy to say "I searched" without actually doing it

**Wrong Examples:**

❌ "I've already checked Pensieve for auth issues"
   - No evidence shown
   - Can't verify this happened

❌ "No relevant memories exist for this problem"
   - No search command shown
   - No output shown
   - Unverifiable claim

❌ "After searching Pensieve, I found some useful entries"
   - Which entries? What IDs?
   - What did they say?
   - This is a summary, not evidence

**Right Examples:**

✅ Shows command, shows output, references specific entries:
```
[Runs: pensieve entry search]

Entry #15: "Connection pool exhaustion under load"
Entry #23: "Nginx timeout configuration for long-running requests"

I'll reference entry #23 since it documents the nginx timeout fix...
```

✅ Shows empty search explicitly:
```
[Runs: pensieve entry search --template workaround_learned]

No entries found

No documented workarounds yet. If we find one, I'll record it.
```

**Enforcement:**

- Before starting ANY task: Show search evidence
- When claiming "no memories": Show the empty output
- When referencing entries: Show entry IDs and titles
- When in doubt: Show the evidence

**Analogy:**

Like the superpowers:verification-before-completion skill requires running tests and showing output before claiming "all tests pass", this skill requires running searches and showing output before claiming "I checked Pensieve."

No evidence = didn't happen.

</CRITICAL>

### Session Start Ritual

**At the beginning of each session, review project memories:**

```bash
# See recent memories for context
pensieve entry search --limit 10

# Check for specific patterns if relevant
pensieve entry search --template pattern_discovered

# Check for known workarounds
pensieve entry search --template workaround_learned
```

**Spend 2-3 minutes reading:** This refreshes context and prevents re-discovering solutions.

### Before Similar Tasks

**When starting a task, search for related memories:**

```bash
# Working on authentication? Check past auth problems
pensieve entry search --field "file_path" --value "auth" --substring

# Working in specific directory? Check memories mentioning it
pensieve entry search --field "files_changed" --value "src/api" --substring

# Specific error type? Search for it
pensieve entry search --field "problem" --value "timeout" --substring
```

### When Stuck

**Hit a blocker? Check if someone solved it before:**

```bash
# Check workarounds
pensieve entry search --template workaround_learned

# Check solved problems
pensieve entry search --template problem_solved

# Check key resources
pensieve entry search --template key_resource
```

**Read the full entries, not just titles.** The "why" and "learned" fields often contain the insight you need.

### Periodic Review

**Weekly or after major milestones:**

```bash
# Review ALL project memories
pensieve entry list --limit 100

# Look for patterns across multiple entries
# Update obsolete workarounds
# Consolidate related learnings
```

## Part 4: Memory Maintenance

### Keeping Memories Fresh

**When better solutions found:**
```bash
# DON'T delete old entry
# DO create new entry referencing the old one

pensieve entry create problem_solved
# In notes: "This supersedes entry abc123... New approach is more reliable because..."
```

**When workarounds become obsolete:**
```bash
# Create entry marking it as resolved
pensieve entry create workaround_learned
# issue: "OBSOLETE: pytest-cov debugger conflict resolved in pytest-cov 3.0"
# workaround: "Upgrade to pytest-cov >=3.0, no --no-cov flag needed anymore"
```

### Quality Checklist

Before recording, verify:
- [ ] **Specific**: Contains concrete details, not vague descriptions
- [ ] **Actionable**: Someone can use this information immediately
- [ ] **Contextualized**: Explains "why" not just "what"
- [ ] **Future-proof**: Will make sense 6 months from now
- [ ] **Non-obvious**: Not something easily Googled or in docs

## Part 5: Integration with Other Skills

### Works With systematic-debugging

After debugging flow completes:
```bash
# If solution was non-obvious, record it
pensieve entry create problem_solved
```

### Works With brainstorming

After design is finalized:
```bash
# Record key architectural decisions
pensieve entry create pattern_discovered
# pattern_name: "Event sourcing for audit trail"
# description: "All state changes emit events..."
```

### Works With test-driven-development

When discovering useful testing patterns:
```bash
# Record testing approaches that work well
pensieve entry create pattern_discovered
# pattern_name: "Fixture-based database testing"
# description: "Use pytest fixtures for test database..."
```

## Part 6: Anti-Patterns - What NOT to Do

### DON'T Record Everything

**❌ WRONG:**
```
Entry 1: "Ran black formatter"
Entry 2: "Fixed typo in comment"
Entry 3: "Updated variable name"
Entry 4: "Installed new library"
```

These are routine actions, not insights.

**✅ RIGHT:**
```
Entry: "Discovered project uses Black with 100-char line length,
enforced in pre-commit hook. Configuration in pyproject.toml:25-30."
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

## Part 7: Practical Workflow Example

### Scenario: Starting Work on New Project

```bash
# 1. Check existing memories (project auto-detected from git root or cwd)
pensieve entry search

# Output: "No entries found"
# → This is a fresh project for you

# 2. Create essential templates (project auto-detected)
pensieve template create
# Create: problem_solved, pattern_discovered, key_resource

# 3. Work begins...
# ... 2 hours later, after reading codebase ...

# 4. Record initial learnings (project auto-detected)
pensieve entry create key_file
# Document main entry points, key directories

pensieve entry create pattern_discovered
# Document API routing pattern you discovered

pensieve entry create key_resource
# Record the architecture doc you found invaluable
```

### Scenario: Solving Complex Bug

```bash
# 1. Hit a bug - authentication failing in CI

# 2. Debug for 1 hour, find it's clock drift issue

# 3. Implement solution with 120s tolerance

# 4. IMMEDIATELY record (don't wait, project auto-detected)
pensieve entry create problem_solved

# Fill in:
# - problem: Clear description of the symptom
# - root_cause: Clock drift in CI environment
# - solution: Specific code changes made
# - files_changed: Exact files and line numbers
# - learned: "Always account for clock skew"
# - reference_url: RFC about timestamp validation

# 5. Future benefit: Next time CI has time-related issues,
#    this memory will save hours
```

### Scenario: Weekly Review

```bash
# Friday afternoon, review week's memories (project auto-detected)

pensieve entry list --limit 50

# Read through entries
# Notice 3 entries about async/await issues
# → Pattern emerging: Team struggles with async

# Record this meta-pattern (project auto-detected)
pensieve entry create key_resource
# resource: "Async/await guide"
# notes: "Team has had 3 separate issues with async in past month.
#         Everyone should review this guide."
```

## Summary: The 3 Rules of Pensieve

1. **Quality Over Quantity**: Record insights, not actions
2. **Context Is King**: Always include the "why"
3. **Future-Focused**: Ask "Will this save time later?"

**Remember**: A well-maintained Pensieve with 10 high-quality entries is more valuable than 100 low-signal entries.

Use this skill consistently, and Pensieve will become your most valuable project resource.
