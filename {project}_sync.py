#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "neo4j>=5.14.0",
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
{PROJECT_NAME} Sync to Neo4j
============================
Syncs data from {API_NAME} API to Neo4j graph database.

Usage:
    uv run {project}_sync.py                    # Full sync (default)
    uv run {project}_sync.py --mode full        # Full sync with index creation
    uv run {project}_sync.py --mode incremental # Incremental sync (TODO: implement)
    uv run {project}_sync.py --help             # Show help

Requirements:
    - Neo4j database running (see .env.example for configuration)
    - {API_NAME} API credentials (see .env.example)
    - Configure .env file with your credentials

Quick Start:
    1. Copy .env.example to .env
    2. Fill in your Neo4j and {API_NAME} credentials
    3. Run: uv run {project}_sync.py

TODO: Customize this script for your specific API
"""

import argparse
import sys
import logging
from dotenv import load_dotenv

# Load environment variables before importing project modules
load_dotenv()

# Import your project modules
from {project}_sync.config import {API}Config, Neo4jConfig
from {project}_sync.orchestrator import SyncOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for sync script"""
    parser = argparse.ArgumentParser(
        description="{PROJECT_NAME} Sync to Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Full sync
  %(prog)s --mode full        # Full sync with index creation
  %(prog)s --mode incremental # Incremental sync
  %(prog)s --skip-indexes     # Skip index creation
        """
    )

    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        default="full",
        help="Sync mode: full (wipe & reload) or incremental (only changes)"
    )

    parser.add_argument(
        "--skip-indexes",
        action="store_true",
        help="Skip creating Neo4j indexes (useful for repeated testing)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - print what would be synced without making changes"
    )

    args = parser.parse_args()

    try:
        # Initialize configurations
        logger.info("=" * 80)
        logger.info("{PROJECT_NAME} SYNC TO NEO4J")
        logger.info("=" * 80)
        logger.info(f"Mode: {args.mode}")
        logger.info(f"Dry run: {args.dry_run}")
        logger.info(f"Create indexes: {not args.skip_indexes}")
        logger.info("=" * 80)

        # TODO: Customize configuration classes for your API
        api_config = {API}Config()
        neo4j_config = Neo4jConfig()

        # Initialize orchestrator
        orchestrator = SyncOrchestrator(api_config, neo4j_config)

        # Run sync based on mode
        if args.mode == "full":
            success = orchestrator.run_full_sync(
                create_indexes=not args.skip_indexes,
                dry_run=args.dry_run
            )
        elif args.mode == "incremental":
            # TODO: Implement incremental sync
            logger.error("Incremental sync not yet implemented")
            logger.info("See task/task_09_incremental_sync.md for implementation guide")
            return 1
        else:
            logger.error(f"Unknown mode: {args.mode}")
            return 1

        if success:
            logger.info("=" * 80)
            logger.info("✓ SYNC COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            return 0
        else:
            logger.error("=" * 80)
            logger.error("✗ SYNC FAILED")
            logger.error("=" * 80)
            return 1

    except KeyboardInterrupt:
        logger.warning("\n⚠ Sync interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"✗ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
