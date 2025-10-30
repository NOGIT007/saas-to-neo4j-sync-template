"""
Migration modules - schema updates and data transformations

Migrations are versioned and run once in sequence. Each migration:
1. Can be run in dry-run mode (plan without applying)
2. Can be skipped if already applied
3. Is idempotent (safe to run multiple times)
4. Includes rollback documentation

Migration Modules:
- migration_001_create_indexes.py: Create indexes and constraints
- migration_002_*.py: TODO - Add more migrations as schema evolves

Pattern:
1. Inherit from Neo4jBase
2. Implement __init__(config, dry_run=False)
3. Implement run() method
4. Support dry-run mode for planning
5. Return stats dict with counts and errors
6. Include rollback notes

Naming:
- migration_NNN_description.py
- NNN: 3-digit zero-padded number (001, 002, 003)
- description: lowercase, underscores, max 50 chars
"""
