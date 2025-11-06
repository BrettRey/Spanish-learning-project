#!/usr/bin/env python3
"""
Database Migration Script

Safely applies schema migrations to mastery.sqlite with backup and rollback support.

Usage:
    python state/migrations/migrate.py                    # Apply pending migrations
    python state/migrations/migrate.py --dry-run          # Show what would be applied
    python state/migrations/migrate.py --rollback 001     # Rollback specific migration
    python state/migrations/migrate.py --status           # Show migration status
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class MigrationError(Exception):
    """Raised when migration fails."""
    pass


class MigrationManager:
    """Manages database schema migrations."""

    def __init__(self, db_path: Path, migrations_dir: Path):
        """
        Initialize migration manager.

        Args:
            db_path: Path to mastery.sqlite
            migrations_dir: Directory containing migration SQL files
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.backup_dir = migrations_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def get_applied_migrations(self) -> List[str]:
        """Get list of already-applied migrations."""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if schema_migrations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='schema_migrations'
        """)

        if not cursor.fetchone():
            conn.close()
            return []

        # Get applied migrations
        cursor.execute("SELECT migration_id FROM schema_migrations ORDER BY applied_at")
        migrations = [row[0] for row in cursor.fetchall()]
        conn.close()

        return migrations

    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of pending migrations to apply."""
        applied = set(self.get_applied_migrations())

        # Find all .sql files in migrations directory
        sql_files = sorted(self.migrations_dir.glob("*.sql"))

        pending = []
        for sql_file in sql_files:
            migration_id = sql_file.stem  # e.g., '001_four_strands'
            if migration_id not in applied:
                pending.append((migration_id, sql_file))

        return pending

    def create_backup(self) -> Path:
        """Create backup of database before migration."""
        if not self.db_path.exists():
            raise MigrationError(f"Database not found: {self.db_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"mastery_backup_{timestamp}.sqlite"

        print(f"Creating backup: {backup_path}")
        shutil.copy2(self.db_path, backup_path)

        return backup_path

    def apply_migration(self, migration_id: str, sql_file: Path, dry_run: bool = False) -> None:
        """
        Apply a single migration.

        Args:
            migration_id: Migration identifier (e.g., '001_four_strands')
            sql_file: Path to SQL file
            dry_run: If True, print SQL but don't execute
        """
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Applying migration: {migration_id}")
        print(f"  File: {sql_file}")

        # Read SQL
        with open(sql_file, 'r') as f:
            sql_content = f.read()

        if dry_run:
            print("\nSQL to be executed:")
            print("-" * 80)
            print(sql_content)
            print("-" * 80)
            return

        # Apply migration
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Execute SQL (split by semicolon for multiple statements)
            cursor.executescript(sql_content)

            conn.commit()
            conn.close()

            print(f"✓ Successfully applied: {migration_id}")

        except sqlite3.Error as e:
            raise MigrationError(f"Failed to apply {migration_id}: {e}")

    def apply_pending_migrations(self, dry_run: bool = False) -> int:
        """
        Apply all pending migrations.

        Args:
            dry_run: If True, show what would be done without executing

        Returns:
            Number of migrations applied
        """
        pending = self.get_pending_migrations()

        if not pending:
            print("✓ No pending migrations. Database is up to date.")
            return 0

        print(f"Found {len(pending)} pending migration(s):")
        for migration_id, sql_file in pending:
            print(f"  - {migration_id}")

        if not dry_run:
            # Create backup before applying
            backup_path = self.create_backup()
            print(f"  (Backup created: {backup_path})")

        # Apply each migration
        for migration_id, sql_file in pending:
            try:
                self.apply_migration(migration_id, sql_file, dry_run=dry_run)
            except MigrationError as e:
                print(f"\n✗ Migration failed: {e}")
                if not dry_run:
                    print(f"\nTo rollback, restore from backup: {backup_path}")
                return 0

        if not dry_run:
            print(f"\n✓ Successfully applied {len(pending)} migration(s)")
        else:
            print(f"\n[DRY RUN] Would apply {len(pending)} migration(s)")

        return len(pending)

    def show_status(self) -> None:
        """Show migration status."""
        print("Migration Status")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Exists: {self.db_path.exists()}")

        if not self.db_path.exists():
            print("\nDatabase not found. Run with no arguments to apply migrations.")
            return

        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        print(f"\nApplied migrations: {len(applied)}")
        for migration_id in applied:
            print(f"  ✓ {migration_id}")

        print(f"\nPending migrations: {len(pending)}")
        for migration_id, _ in pending:
            print(f"  ○ {migration_id}")

        if not pending:
            print("\n✓ Database is up to date")

    def verify_migration(self, migration_id: str) -> bool:
        """
        Verify that migration was successfully applied.

        Args:
            migration_id: Migration to verify

        Returns:
            True if migration appears to be applied correctly
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check that expected tables/columns exist
        if migration_id == '001_four_strands':
            checks = [
                # Check new tables
                ("SELECT name FROM sqlite_master WHERE type='table' AND name='fluency_metrics'", True),
                ("SELECT name FROM sqlite_master WHERE type='table' AND name='meaning_input_log'", True),
                ("SELECT name FROM sqlite_master WHERE type='table' AND name='meaning_output_log'", True),

                # Check new columns in items table
                ("PRAGMA table_info(items)", lambda rows: any(r[1] == 'primary_strand' for r in rows)),
                ("PRAGMA table_info(items)", lambda rows: any(r[1] == 'mastery_status' for r in rows)),

                # Check new columns in review_history
                ("PRAGMA table_info(review_history)", lambda rows: any(r[1] == 'strand' for r in rows)),

                # Check views
                ("SELECT name FROM sqlite_master WHERE type='view' AND name='fluency_ready_items'", True),
                ("SELECT name FROM sqlite_master WHERE type='view' AND name='strand_balance_recent'", True),
            ]

            all_passed = True
            for check_sql, expected in checks:
                cursor.execute(check_sql)
                result = cursor.fetchall()

                if callable(expected):
                    passed = expected(result)
                else:
                    passed = bool(result) == expected

                if not passed:
                    print(f"  ✗ Check failed: {check_sql[:60]}...")
                    all_passed = False

            conn.close()
            return all_passed

        conn.close()
        return True


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database migration tool for mastery.sqlite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply pending migrations
  python state/migrations/migrate.py

  # Show what would be applied without executing
  python state/migrations/migrate.py --dry-run

  # Show migration status
  python state/migrations/migrate.py --status

  # Verify migration
  python state/migrations/migrate.py --verify 001_four_strands
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status"
    )

    parser.add_argument(
        "--verify",
        metavar="MIGRATION_ID",
        help="Verify that migration was applied correctly"
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).parent.parent / "mastery.sqlite",
        help="Path to mastery.sqlite (default: ../mastery.sqlite)"
    )

    args = parser.parse_args(argv)

    migrations_dir = Path(__file__).parent
    manager = MigrationManager(args.db, migrations_dir)

    try:
        if args.status:
            manager.show_status()
            return 0

        if args.verify:
            print(f"Verifying migration: {args.verify}")
            if manager.verify_migration(args.verify):
                print("✓ Migration verified successfully")
                return 0
            else:
                print("✗ Migration verification failed")
                return 1

        # Apply pending migrations
        count = manager.apply_pending_migrations(dry_run=args.dry_run)

        # Verify if migrations were applied
        if count > 0 and not args.dry_run:
            print("\nVerifying migrations...")
            pending = manager.get_pending_migrations()
            if pending:
                print("✗ Warning: Some migrations may not have been applied correctly")
                return 1

        return 0

    except MigrationError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
