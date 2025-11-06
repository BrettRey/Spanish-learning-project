# Database Migrations

This directory contains schema migrations for the mastery.sqlite database.

## Overview

Migrations provide a safe, versioned way to evolve the database schema over time. Each migration:
- Has a unique ID (e.g., `001_four_strands`)
- Contains SQL to apply changes
- Is tracked in the `schema_migrations` table
- Creates automatic backups before execution

## Migration Files

- `001_four_strands.sql` - Adds Four Strands support (strand tracking, fluency metrics, mastery status)
- `migrate.py` - Python script to apply migrations
- `backups/` - Automatic backups created before each migration

## Usage

### Apply Pending Migrations

```bash
# Show what migrations would be applied
python state/migrations/migrate.py --dry-run

# Apply all pending migrations
python state/migrations/migrate.py
```

### Check Status

```bash
# See which migrations are applied/pending
python state/migrations/migrate.py --status
```

### Verify Migration

```bash
# Verify a migration was applied correctly
python state/migrations/migrate.py --verify 001_four_strands
```

### Rollback (Manual)

If a migration fails or needs to be rolled back:

```bash
# 1. Find the backup created before migration
ls -lt state/migrations/backups/

# 2. Restore from backup
cp state/migrations/backups/mastery_backup_YYYYMMDD_HHMMSS.sqlite state/mastery.sqlite
```

## Creating New Migrations

### 1. Create SQL File

Create a new `.sql` file in this directory with format: `NNN_description.sql`

```sql
-- Migration NNN: Description
-- Date: YYYY-MM-DD
-- Description: What this migration does

-- Add your SQL here
ALTER TABLE items ADD COLUMN new_field TEXT;

-- Track migration
INSERT INTO schema_migrations (migration_id, description)
VALUES ('NNN_description', 'Brief description');
```

### 2. Test Migration

```bash
# Test in dry-run mode first
python state/migrations/migrate.py --dry-run

# Apply if everything looks good
python state/migrations/migrate.py

# Verify it worked
python state/migrations/migrate.py --verify NNN_description
```

## Migration 001: Four Strands

**Applied**: 2025-11-05
**Reference**: `FOUR_STRANDS_REDESIGN.md`

### Changes

**New Tables:**
- `fluency_metrics` - Tracks speed/automaticity (WPM, pauses, self-assessment)
- `meaning_input_log` - Tracks comprehension practice
- `meaning_output_log` - Tracks communication practice
- `schema_migrations` - Tracks applied migrations

**Extended Tables:**
- `items` table:
  - `primary_strand` - Strand classification
  - `mastery_status` - Learning status (new/learning/mastered/fluency_ready)
  - `last_mastery_check` - When status was last evaluated

- `review_history` table:
  - `strand` - Strand context for review
  - `exercise_type` - Type of exercise

**New Views:**
- `fluency_ready_items` - Items ready for fluency practice (stability ≥21d, reps ≥3)
- `learning_items` - Items currently being learned
- `strand_balance_recent` - Strand distribution over last 10 sessions
- `strand_balance_summary` - Percentage balance across strands
- `items_needing_mastery_check` - Items that may have reached mastery

### Verification

```bash
# Verify migration applied correctly
python state/migrations/migrate.py --verify 001_four_strands

# Check new schema
sqlite3 state/mastery.sqlite "PRAGMA table_info(items);"
sqlite3 state/mastery.sqlite "SELECT * FROM fluency_ready_items LIMIT 5;"
sqlite3 state/mastery.sqlite "SELECT * FROM strand_balance_summary;"
```

## Safety Features

1. **Automatic Backups**: Created before each migration run
2. **Dry-run Mode**: Preview changes without executing
3. **Verification**: Check that migration was applied correctly
4. **Idempotent SQL**: Uses `IF NOT EXISTS` / `IF EXISTS` where possible
5. **Transaction Safety**: Each migration runs in a transaction (implicit with executescript)

## Troubleshooting

### Migration Failed

If a migration fails mid-execution:

1. Check the error message
2. Restore from backup: `cp state/migrations/backups/[latest].sqlite state/mastery.sqlite`
3. Fix the SQL in the migration file
4. Remove the failed migration from `schema_migrations` table if it was partially recorded
5. Re-run the migration

### "Migration already applied" but schema is wrong

This can happen if migration was manually applied or partially completed:

```bash
# Check what's in schema_migrations
sqlite3 state/mastery.sqlite "SELECT * FROM schema_migrations;"

# If needed, remove the record and re-apply
sqlite3 state/mastery.sqlite "DELETE FROM schema_migrations WHERE migration_id = '001_four_strands';"
python state/migrations/migrate.py
```

### Views not showing data

Views depend on having data in the underlying tables. If views are empty, that's expected until:
- Items have `mastery_status` set
- Reviews have `strand` recorded
- Fluency exercises have been logged

## Best Practices

1. **One migration per logical change**: Don't combine unrelated changes
2. **Test on a copy first**: Use a copy of production database
3. **Keep migrations small**: Easier to debug and rollback
4. **Document assumptions**: Comment what data you expect to exist
5. **Don't modify old migrations**: Create new ones to fix issues
6. **Check for data migration needs**: ALTER TABLE adds columns, but may need to populate them

## Future Migrations

When adding new migrations:

1. Use next sequential number (002, 003, etc.)
2. Update this README with migration details
3. Reference relevant design docs (like FOUR_STRANDS_REDESIGN.md)
4. Test thoroughly in dry-run mode first
5. Commit migration SQL and updated schema.sql together
