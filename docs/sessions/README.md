# Session Transcripts and Analysis

This directory contains real language learning session transcripts and associated data exports for analysis and improvement.

## Purpose

Recording actual sessions helps us:
1. **Identify UX friction points** - Where do learners get confused or frustrated?
2. **Validate pedagogical approach** - Are corrections appropriate? Is tone right?
3. **Test strand balance** - Are activities properly categorized and signaled?
4. **Improve coaching instructions** - What patterns emerge across sessions?
5. **Track quality assessment accuracy** - Are quality ratings (0-5) consistent and fair?

## File Naming Convention

### Transcripts
- Format: `transcript-YYYYMMDD[-N].txt` or `.md`
- Example: `transcript-20251106.txt`
- If multiple sessions in one day: `transcript-20251106-1.txt`, `transcript-20251106-2.txt`

### Data Exports
- Format: `{table_name}-YYYYMMDD.json`
- Example: `items-20251106.json`, `session_log-20251106.json`, `exercise_log-20251106.json`

### Analysis Notes
- Format: `analysis-YYYYMMDD.md`
- Example: `analysis-20251106.md`

## What to Include

### In Transcripts
- Full conversation between coach and learner
- Any technical errors or friction points
- Learner feedback/pushback (very valuable!)
- Timestamps if available

### In Data Exports
Export relevant tables from `state/mastery.sqlite` after sessions:

```bash
# Export session data (run from project root on local machine)
python -c "
import sqlite3
import json
from pathlib import Path
from datetime import datetime

date_str = datetime.now().strftime('%Y%m%d')
conn = sqlite3.connect('state/mastery.sqlite')
conn.row_factory = sqlite3.Row

# Export items (shows strand assignments)
items = [dict(row) for row in conn.execute('SELECT * FROM items')]
Path(f'docs/sessions/items-{date_str}.json').write_text(json.dumps(items, indent=2, default=str))

# Export session_log (shows session metadata)
sessions = [dict(row) for row in conn.execute('SELECT * FROM session_log ORDER BY started_at DESC LIMIT 5')]
Path(f'docs/sessions/session_log-{date_str}.json').write_text(json.dumps(sessions, indent=2, default=str))

# Export exercise_log (shows what was practiced and quality ratings)
exercises = [dict(row) for row in conn.execute('SELECT * FROM exercise_log ORDER BY completed_at DESC LIMIT 20')]
Path(f'docs/sessions/exercise_log-{date_str}.json').write_text(json.dumps(exercises, indent=2, default=str))

conn.close()
print(f'Exported session data to docs/sessions/*-{date_str}.json')
"
```

### In Analysis Notes
- Key issues identified
- Suggested fixes
- Design decisions made
- Open questions

## Privacy

**Never commit:**
- Personal information beyond what's needed for analysis
- Embarrassing learner errors (keep examples anonymized)
- Real names (use pseudonyms if needed)

**Okay to commit:**
- Representative conversation excerpts
- Error patterns (anonymized)
- Quality assessments and strand assignments
- System bugs and friction points

## Current Sessions

- **2025-11-06**: First real session, identified multiple pedagogical and technical issues
  - See `transcript-20251106.txt` for full conversation
  - Key findings documented in TODO.md and CHANGELOG.md

---

*This directory helps improve the coaching experience through empirical observation of real sessions.*
