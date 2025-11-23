---
title: "Session 1: Discovering Date Ambiguity"
weight: 1
---

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

## Key Takeaway

This session demonstrates how a "working" piece of code can have subtle bugs that only surface with certain data. By recording this learning in pensieve, future Claude sessions will be reminded of this gotcha when encountering similar date parsing scenarios.
