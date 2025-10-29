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
2. Search for existing memories: `pensieve entry search --project $(pwd)`
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
2. Search for project memories: `pensieve entry search --project $(pwd)`
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
pensieve entry search --project $(pwd)
```

If memories exist, read them to understand what past agents learned. Then skip to Part 2.

### Step 2: Create Project-Specific Templates

Create 3-5 templates based on what will be useful for THIS project. Don't create templates "just in case" - create them when you have something to record.

#### Recommended Template Types:

**1. problem_solved** - For complex bugs and technical challenges
```bash
pensieve template create --project $(pwd)

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
pensieve template create --project $(pwd)

# Fields:
# - pattern_name (text, required, max 100): Short name
# - description (text, required, max 500): What is it?
# - location (file_reference, required): Where to find it
# - why_useful (text, required, max 300): When/why to use it
# - example_code (text, optional, max 1000): Code snippet or reference
```

**3. workaround_learned** - For tool/library issues and workarounds
```bash
pensieve template create --project $(pwd)

# Fields:
# - issue (text, required, max 300): What doesn't work?
# - workaround (text, required, max 500): How to work around it
# - why_needed (text, required, max 300): Root cause if known
# - reference_url (url, optional): Issue tracker link
# - discovered_at (timestamp, required, auto_now: yes)
```

**4. key_resource** - For important documentation and references
```bash
pensieve template create --project $(pwd)

# Fields:
# - resource_name (text, required, max 100): Name/title
# - resource_url (url, required): Link
# - what_it_covers (text, required, max 300): Topics covered
# - when_useful (text, required, max 300): When to reference it
# - notes (text, optional, max 500): Additional context
```

**5. key_file** - For important files agents should know about
```bash
pensieve template create --project $(pwd)

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
pensieve entry create key_file --project $(pwd)

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
pensieve entry create <template-name> --project $(pwd)
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
  2. Run: pensieve entry create problem_solved --project $(pwd) \
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
  2. Run: pensieve entry create pattern_discovered --project $(pwd) \
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
  2. Run: pensieve entry create workaround_learned --project $(pwd) \
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
2. Immediately run: `pensieve entry search --project $(pwd)`
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

### Session Start Ritual

**At the beginning of each session, review project memories:**

```bash
# See recent memories for context
pensieve entry search --project $(pwd) --limit 10

# Check for specific patterns if relevant
pensieve entry search --project $(pwd) --template pattern_discovered

# Check for known workarounds
pensieve entry search --project $(pwd) --template workaround_learned
```

**Spend 2-3 minutes reading:** This refreshes context and prevents re-discovering solutions.

### Before Similar Tasks

**When starting a task, search for related memories:**

```bash
# Working on authentication? Check past auth problems
pensieve entry search --project $(pwd) --field "file_path" --value "auth" --substring

# Working in specific directory? Check memories mentioning it
pensieve entry search --project $(pwd) --field "files_changed" --value "src/api" --substring

# Specific error type? Search for it
pensieve entry search --project $(pwd) --field "problem" --value "timeout" --substring
```

### When Stuck

**Hit a blocker? Check if someone solved it before:**

```bash
# Check workarounds
pensieve entry search --project $(pwd) --template workaround_learned

# Check solved problems
pensieve entry search --project $(pwd) --template problem_solved

# Check key resources
pensieve entry search --project $(pwd) --template key_resource
```

**Read the full entries, not just titles.** The "why" and "learned" fields often contain the insight you need.

### Periodic Review

**Weekly or after major milestones:**

```bash
# Review ALL project memories
pensieve entry list --project $(pwd) --limit 100

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

pensieve entry create problem_solved --project $(pwd)
# In notes: "This supersedes entry abc123... New approach is more reliable because..."
```

**When workarounds become obsolete:**
```bash
# Create entry marking it as resolved
pensieve entry create workaround_learned --project $(pwd)
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
pensieve entry create problem_solved --project $(pwd)
```

### Works With brainstorming

After design is finalized:
```bash
# Record key architectural decisions
pensieve entry create pattern_discovered --project $(pwd)
# pattern_name: "Event sourcing for audit trail"
# description: "All state changes emit events..."
```

### Works With test-driven-development

When discovering useful testing patterns:
```bash
# Record testing approaches that work well
pensieve entry create pattern_discovered --project $(pwd)
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
# 1. Check existing memories
pensieve entry search --project ~/projects/new-api

# Output: "No entries found"
# → This is a fresh project for you

# 2. Create essential templates
pensieve template create --project ~/projects/new-api
# Create: problem_solved, pattern_discovered, key_resource

# 3. Work begins...
# ... 2 hours later, after reading codebase ...

# 4. Record initial learnings
pensieve entry create key_file --project ~/projects/new-api
# Document main entry points, key directories

pensieve entry create pattern_discovered --project ~/projects/new-api
# Document API routing pattern you discovered

pensieve entry create key_resource --project ~/projects/new-api
# Record the architecture doc you found invaluable
```

### Scenario: Solving Complex Bug

```bash
# 1. Hit a bug - authentication failing in CI

# 2. Debug for 1 hour, find it's clock drift issue

# 3. Implement solution with 120s tolerance

# 4. IMMEDIATELY record (don't wait)
pensieve entry create problem_solved --project ~/projects/my-api

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
# Friday afternoon, review week's memories

pensieve entry list --project ~/projects/my-api --limit 50

# Read through entries
# Notice 3 entries about async/await issues
# → Pattern emerging: Team struggles with async

# Record this meta-pattern
pensieve entry create key_resource --project ~/projects/my-api
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
