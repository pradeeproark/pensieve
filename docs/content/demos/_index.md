---
title: "Demo"
---

Watch Pensieve in action with Claude Code. This demonstration shows a real conversation extracted from Claude Code sessions, showcasing how Pensieve builds knowledge across multiple interactions.

<div class="demo-grid">

<div class="demo-session">

<h3 id="session-1">Session 1: Discovering Date Ambiguity</h3>

In this session, we discover a subtle but dangerous bug in CSV date parsing - ambiguous dates that can silently corrupt data.

<div class="story">

<div class="story-turn user">
<div class="role">👤 User</div>

Run the csv_processor.py and check if it's working

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

I'll follow the mandatory protocol first by searching for relevant memories.

```
$ pensieve entry search --limit 5
No entries found for this project
```

Let me run the processor:

```
$ python csv_processor.py

Processing us_sales.csv...
  Loaded 5 records
  First record: {'id': '1', 'product': 'Widget A',
                 'date': datetime(2024, 1, 5, 0, 0), 'amount': '150.00'}
```

The CSV processor is working correctly. It processed us_sales.csv with 5 records. Would you like me to look at the processor code or test it with different data?

</div>

<div class="story-turn user">
<div class="role">👤 User</div>

Wait, the date 01/05/2024 - is that January 5th or May 1st? How do we know?

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

Excellent question! The output shows `datetime(2024, 1, 5, 0, 0)` which is January 5th - so it's using US format (MM/DD/YYYY). Let me check the code...

The parser tries multiple formats:
```python
formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]
```

Since US format is listed first, it wins for ambiguous dates.

<div class="insight">

This is a classic date parsing bug! Ambiguous dates like "01/05/2024" can be parsed both ways without error. The code silently assumes US format, which could corrupt data from European sources.

</div>

The only way to know the correct interpretation is from context. The file is named `us_sales.csv` and row 5 has `03/15/2024` - that can only be March 15th (no 15th month!), proving the data is US format.

However, the code is fragile. If you had a European file with all dates ≤12 in the day position, it would silently misparse everything.

</div>

<div class="story-turn user">
<div class="role">👤 User</div>

Fix the parser to require explicit locale, and remember this learning

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

I'll fix this by requiring explicit date formats - no more guessing.

<span class="action">✏️ Edited csv_processor.py to add explicit DateFormat enum (ISO, US, EU) and modified parse_date() to require format specification instead of trying multiple formats.</span>

<span class="action">🧠 Recording this learning with pensieve...</span>

```
$ pensieve entry create --template pattern_discovered

Created entry: Date Parsing Ambiguity
Tags: date-parsing, data-validation, csv

Summary: Ambiguous date formats like MM/DD vs DD/MM can silently
corrupt data. Always require explicit locale/format specification
rather than trying multiple formats.
```

<span class="action">✓ Remembered! Future sessions will recall this when working with date parsing.</span>

</div>

</div>

</div>

<div class="demo-session">

<h3 id="session-2">Session 2: Adding European Data</h3>

In this session, we add support for European order data. Watch how pensieve recalls the date parsing lesson from Session 1 and prevents us from making the same mistake.

<div class="story">

<div class="story-turn user">
<div class="role">👤 User</div>

I need to add support for processing eu_orders.csv

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

I'll search for any relevant memories before starting.

```
$ pensieve entry search --limit 5

Found 1 entry:
  ID: 1a0501ad-48ad-41c2-b73a-c85d711dd6d2
  Template: pattern_discovered
  Tags: date-parsing, data-validation, csv
```

<div class="insight">

Found a relevant memory! Let me review it before proceeding with European data.

</div>

```
$ pensieve entry show 1a0501ad-...

Pattern: Date Parsing Ambiguity
Summary: Ambiguous date formats like MM/DD vs DD/MM can silently
corrupt data. Always require explicit locale/format specification.

When it applies: Any date parsing from external sources
Recommended approach: Use explicit DateFormat constants, never guess
```

This is directly relevant! The existing code already handles this with explicit `DateFormat.US` and `DateFormat.EU` constants. Let me check the current implementation...

</div>

<div class="story-turn user">
<div class="role">👤 User</div>

Can you update main() to process the EU file too?

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

Based on the memory from our previous session, I know EU dates use DD/MM/YYYY format. The code already has `DateFormat.EU` - I just need to add the EU file processing with the correct format.

<span class="action">✏️ Edited csv_processor.py to add EU file processing in main() using DateFormat.EU for proper DD/MM/YYYY parsing.</span>

Let me verify it works:

```
$ python csv_processor.py

Processing us_sales.csv (US locale)...
  Loaded 5 records
  First record: {'id': '1', 'product': 'Widget A',
                 'date': datetime(2024, 1, 5, 0, 0), 'amount': '150.00'}

Processing eu_orders.csv (EU locale)...
  Loaded 5 records
  First record: {'order_id': 'EU-001', 'customer': 'Müller GmbH',
                 'order_date': datetime(2024, 1, 5, 0, 0), 'total': '1250.00'}
```

Both files processed correctly. Notice that `05/01/2024` in the EU file is correctly parsed as January 5th (DD/MM/YYYY), not May 1st.

<div class="insight">

Without the memory from Session 1, I might have just used the same format for both files or tried to "auto-detect" - which would silently corrupt the EU dates. The pensieve entry reminded me to always be explicit about date formats.

</div>

</div>

<div class="story-turn user">
<div class="role">👤 User</div>

Remember this working solution for EU dates

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

<span class="action">🧠 Recording this confirmation to pensieve...</span>

I found the related entry about date parsing. Let me record this confirmation that the pattern works with EU dates, and link it to the existing entry.

```
✓ Entry Recorded:
  ID: 4961b089-3627-4c41-a90d-a8b0e59d5f2f
  Pattern: "Locale-Aware CSV Processing for European Dates"
  Tags: date-parsing, european-dates, locale-handling
  Linked to: Original pattern (augments relationship)
```

<div class="insight">

**Knowledge Graph Building:** Notice how this new entry links to the existing Session 1 memory using the "augments" relationship. This creates a knowledge graph where each session builds on previous learnings.

</div>

</div>

</div>

</div>

<div class="demo-session">

<h3 id="session-3">Session 3: Excel Serial Dates</h3>

In this session, we encounter Excel serial dates. Watch how pensieve automatically surfaces BOTH previous date-related memories, demonstrating the compounding value of accumulated knowledge.

<div class="story">

<div class="story-turn user">
<div class="role">👤 User</div>

Process the excel_export.csv file

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

Let me search for relevant memories first.

```
$ pensieve entry search --limit 5

Found 2 entries:
  ID: 4961b089-3627-4c41-a90d-a8b0e59d5f2f
  Template: pattern_discovered
  Tags: date-parsing, european-dates, locale-handling

  ID: 1a0501ad-48ad-41c2-b73a-c85d711dd6d2
  Template: pattern_discovered
  Tags: date-parsing, data-validation, csv
```

<div class="insight">

**Pattern Recognition Across Sessions:** I've dealt with date formats twice before! Let me review both memories to understand what I've learned about date handling in this codebase.

</div>

Let me check what these previous learnings say...

```
Pattern: Date Parsing Ambiguity
Summary: Ambiguous date formats like MM/DD vs DD/MM can silently
corrupt data. Always require explicit locale/format specification.
```

```
Pattern: Locale-Aware CSV Processing for European Dates
Summary: Confirmed that explicit DateFormat constants work correctly
for EU dates. Always be explicit about date formats.
```

Good! The code already handles US and EU formats explicitly. Let me process the Excel file.

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

```
$ python csv_processor.py

Processing excel_export.csv...
  Error: Cannot parse date '45292' with format '%Y-%m-%d'
```

Interesting! Excel dates are appearing as numbers. Let me investigate...

```python
# Example data from excel_export.csv:
# 45292, Widget X, 1200.00
# 45293, Widget Y, 850.50
```

<div class="insight">

**New Pattern:** Excel serial dates! These are numeric values representing days since 1899-12-30. The value 45292 is actually November 21, 2023.

This is different from the MM/DD vs DD/MM ambiguity we've handled before - it's a completely different date encoding system that requires numeric handling.

</div>

Let me add support for Excel serial dates while maintaining the explicit format approach from our previous learnings.

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

I'll update the parse_date function to handle numeric Excel dates:

<span class="action">✏️ Edited csv_processor.py parse_date() to add try-except logic: first attempt parsing as Excel serial number (days since 1899-12-30), then fall back to explicit format string parsing.</span>

Now let me test it:

```
$ python csv_processor.py

Processing excel_export.csv...
  Loaded 5 records
  First record: {'serial_id': 'EX-001', 'product': 'Widget X',
                 'date': datetime(2023, 11, 21, 0, 0), 'amount': '1200.00'}
```

Perfect! The serial date 45292 is correctly parsed as November 21, 2023.

</div>

<div class="story-turn user">
<div class="role">👤 User</div>

Great! Remember this solution

</div>

<div class="story-turn assistant">
<div class="role">🤖 Claude</div>

<span class="action">🧠 Evaluating and recording learnings to pensieve...</span>

Let me assess this learning against the rubric:

**Evaluation:**
- ✓ **Specific**: Concrete solution for Excel serial dates with exact implementation
- ✓ **Reusable**: Pattern applies to any Excel CSV export
- ✓ **Linked**: Relates to previous date parsing memories (Sessions 1 & 2)
- ✓ **Contextualized**: Tied to specific files and code location
- ✓ **Proven**: Working solution, not theoretical

This meets the criteria for recording. Creating entry...

```
✓ Entry Recorded:
  ID: 397ec7ff-8e3e-40bd-b811-2c0b92d4d440
  Template: problem_solved
  Problem: Excel dates in CSV failed to parse - numeric values like 45292
  Solution: Try-except pattern to attempt float conversion first
  Tags: csv, date-parsing, excel
  Linked to previous sessions
```

<div class="insight">

**Knowledge Graph Evolution:** This is the third date-related learning in our knowledge graph. Each session builds on previous learnings, demonstrating how Pensieve accumulates expertise over time through autonomous knowledge management.

</div>

</div>

</div>

</div>

</div>
