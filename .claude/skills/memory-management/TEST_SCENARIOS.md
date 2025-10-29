# Proactive Memory Recording - Test Scenarios

This document outlines test scenarios to validate the proactive memory recording system.

## Prerequisites

1. Hook scripts installed: `~/.claude/hooks/session-memory-reminder.sh` and `memory-check.sh`
2. Hooks configured in `~/.claude/settings.json` (see EXAMPLE_SETTINGS.json)
3. Pensieve installed and accessible
4. memory-management skill loaded

## Test Scenario 1: Session Start Memory Retrieval

**Setup:**
- Project with existing Pensieve entries
- Fresh Claude session

**Expected Behavior:**

1. **Hook fires**: SessionStart hook executes when session begins
2. **Claude sees reminder**: `📝 Session Start: Use memory-management skill...`
3. **Claude retrieves memories**: Runs `pensieve entry search --project $(pwd)`
4. **Claude reviews context**: Reads 2-3 recent entries
5. **Claude acknowledges**: Mentions to user that context has been restored

**Validation:**
- [ ] Hook reminder appears at session start
- [ ] Claude proactively searches for memories
- [ ] Claude mentions relevant memories in context
- [ ] User doesn't need to ask for memory retrieval

**Test Command:**
```bash
# In a project with memories
cd ~/Documents/Projects/Mine/kuberan/pensieve
# Start new Claude session
# Observe if Claude automatically retrieves memories
```

## Test Scenario 2: Complex Problem Solved (3/3 Rubric)

**Setup:**
- Claude solves a complex, non-obvious bug
- Solution takes >30 minutes
- Root cause is not documented

**Expected Behavior:**

1. **Claude solves problem**: Implements fix after investigation
2. **Stop hook fires**: `💡 Memory Check: If you just solved...`
3. **Claude applies rubric**:
   - Complexity? YES (took 45 minutes)
   - Novelty? YES (not documented)
   - Reusability? YES (similar issues likely)
   - Score: 3/3
4. **Claude notifies user**: "I'm spawning a subagent to record this to Pensieve..."
5. **Claude spawns subagent**: Uses Template 1 (Problem Solved)
6. **Claude continues work**: Doesn't wait for subagent
7. **Subagent records**: Creates Pensieve entry
8. **Subagent reports back**: Returns entry ID

**Validation:**
- [ ] Hook reminder appears after problem solved
- [ ] Claude evaluates with rubric (shows 3/3 score)
- [ ] Subagent spawned (not inline recording)
- [ ] Main Claude doesn't block on recording
- [ ] Pensieve entry created successfully
- [ ] Entry contains: problem, root_cause, solution, files_changed, learned

**Test Example:**
```bash
# Simulate: "Fix authentication timeout in CI pipeline"
# Expected pensieve entry:
# - problem: "Auth tokens timing out in CI but not locally"
# - root_cause: "Clock drift in CI environment"
# - solution: "Added 120s tolerance window to token validation"
# - learned: "Always account for clock skew in distributed systems"
```

## Test Scenario 3: Routine Task (0/3 Rubric)

**Setup:**
- Claude completes routine task (e.g., fixing import error)
- Solution is trivial, well-known

**Expected Behavior:**

1. **Claude completes task**: Fixes import error
2. **Stop hook fires**: `💡 Memory Check...`
3. **Claude applies rubric**:
   - Complexity? NO (took 10 seconds)
   - Novelty? NO (standard Python error)
   - Reusability? NO (trivial issue)
   - Score: 0/3
4. **Claude skips recording**: Acknowledges hook but doesn't record
5. **Claude continues**: No subagent spawned

**Validation:**
- [ ] Hook reminder appears
- [ ] Claude evaluates and determines 0/3 score
- [ ] No recording happens
- [ ] No subagent spawned
- [ ] Workflow continues smoothly

## Test Scenario 4: Borderline Case (2/3 Rubric)

**Setup:**
- Claude discovers a pattern in codebase
- Pattern is somewhat obvious but not explicitly documented
- Moderate complexity

**Expected Behavior:**

1. **Claude discovers pattern**: Finds naming convention used across files
2. **Stop hook fires**: `💡 Memory Check...`
3. **Claude applies rubric**:
   - Complexity? YES (took time to identify)
   - Novelty? MAYBE (pattern exists but not documented)
   - Reusability? YES (helps maintain consistency)
   - Score: 2/3
4. **Claude asks user**: Uses AskUserQuestion
   ```
   "I just discovered a naming pattern for API routes. Should I record this to Pensieve?"
   Options: [Yes, record it] [No, skip it]
   ```
5. **User decides**: Selects option
6. **Claude follows decision**: Records if yes, skips if no

**Validation:**
- [ ] Hook reminder appears
- [ ] Claude evaluates rubric and gets 2/3
- [ ] AskUserQuestion presented to user
- [ ] User choice is respected
- [ ] Recording happens only if user confirms

## Test Scenario 5: Pattern Discovery During Exploration

**Setup:**
- Claude uses Explore agent to understand codebase
- Discovers architectural pattern

**Expected Behavior:**

1. **Claude explores code**: Uses Grep/Glob/Read extensively
2. **Claude discovers pattern**: Identifies dependency injection approach
3. **Stop hook fires**: `💡 Memory Check...`
4. **Claude applies rubric**:
   - Complexity? YES (non-obvious pattern)
   - Novelty? YES (not in docs)
   - Reusability? YES (important for new features)
   - Score: 3/3
5. **Claude spawns subagent**: Uses Template 2 (Pattern Discovered)
6. **Subagent records**: Creates entry with pattern details

**Validation:**
- [ ] Pattern recognized as memory-worthy
- [ ] Subagent spawned with correct template
- [ ] Entry contains: pattern_name, description, location, why_useful
- [ ] Main work continues without blocking

## Test Scenario 6: Git Commit with Significant Changes

**Setup:**
- Claude completes feature with >50 lines changed
- Feature involved solving non-trivial problem
- About to commit

**Expected Behavior:**

1. **Claude completes feature**: Implements and tests
2. **User asks to commit**: "Please commit these changes"
3. **Stop hook fires**: Before/after commit
4. **Claude applies rubric**: Evaluates if changes merit recording
5. **If worthy**: Spawns subagent before commit
6. **Creates commit**: With proper message
7. **Subagent records**: Captures solution details

**Validation:**
- [ ] Hook reminds before commit
- [ ] Claude checks if commit represents learning
- [ ] Recording happens for significant work
- [ ] Routine commits don't trigger recording
- [ ] Commit proceeds normally

## Test Scenario 7: Workaround Discovery

**Setup:**
- Claude encounters tool/library issue
- Finds workaround after investigation

**Expected Behavior:**

1. **Claude hits issue**: pytest-cov breaks debugger
2. **Claude finds workaround**: Use --no-cov flag
3. **Stop hook fires**: `💡 Memory Check...`
4. **Claude applies rubric**: 3/3 (complex, novel, reusable)
5. **Claude spawns subagent**: Uses Template 3 (Workaround)
6. **Subagent records**: Creates workaround_learned entry

**Validation:**
- [ ] Workaround recognized as worth recording
- [ ] Correct template used (Template 3)
- [ ] Entry contains: issue, workaround, why_needed, reference_url
- [ ] Future agents can find this workaround

## Performance Validation

### Success Metrics

After testing all scenarios, verify:

1. **Recall (Catching Important Moments)**: >90%
   - Count: Important learnings that were recorded / Total important learnings
   - Test: Review all complex problems solved, patterns discovered
   - Target: Claude should catch 9/10 important moments

2. **Precision (Avoiding Low-Value Recordings)**: <20% false positives
   - Count: Low-value entries recorded / Total entries recorded
   - Test: Review all Pensieve entries for signal quality
   - Target: >80% of entries should be high-value

3. **Non-Disruption**: 100%
   - Count: Times main work blocked on recording / Total recordings
   - Test: Observe if Claude ever waits for subagent
   - Target: 0 instances of blocking

4. **User Confirmation Rate**: 10-20%
   - Count: Times user asked for confirmation / Total potential recordings
   - Test: Track AskUserQuestion usage
   - Target: Only borderline cases (2/3) go to user

### Manual Testing Checklist

- [ ] Test all 7 scenarios above
- [ ] Verify hook scripts execute correctly
- [ ] Confirm subagents spawn properly
- [ ] Check Pensieve entries are created
- [ ] Validate entry quality (specific, actionable, contextualized)
- [ ] Ensure main workflow never blocks
- [ ] Verify rubric is applied consistently
- [ ] Confirm user asked only on borderline cases

### Integration Testing

Test with real development work:

1. **Week 1**: Enable hooks, observe natural workflow
2. **Week 2**: Review all Pensieve entries created
3. **Analysis**: Calculate recall, precision, non-disruption metrics
4. **Adjustment**: Refine rubric thresholds if needed

## Troubleshooting

### Hook Not Firing

**Symptom**: No reminder messages appear
**Check**:
- Hooks configured in settings.json?
- Script paths absolute and correct?
- Scripts executable (chmod +x)?

### Too Many Reminders

**Symptom**: Hook fires too frequently, feels spammy
**Solution**:
- Disable Stop hook
- Use SubagentStop hook instead
- Or increase complexity threshold in rubric

### Too Few Recordings

**Symptom**: Important learnings not recorded
**Check**:
- Rubric thresholds too strict?
- Claude applying rubric correctly?
- Lower complexity threshold from 30min to 20min

### Too Many Low-Value Recordings

**Symptom**: Pensieve filled with routine tasks
**Check**:
- Rubric not being applied?
- Raise complexity threshold to 45min
- Emphasize novelty criterion

## Next Steps

After validating test scenarios:

1. **Deploy to real projects**: Use in daily development for 1-2 weeks
2. **Collect metrics**: Track recall, precision, user satisfaction
3. **Iterate**: Adjust rubric based on real-world usage
4. **Document learnings**: Update this test document with findings
5. **Share**: Contribute improvements back to skill

## Notes

- These scenarios test the happy path
- Edge cases (network errors, Pensieve unavailable) need separate testing
- Performance will improve as Claude learns the rubric
- User feedback is critical for calibration
