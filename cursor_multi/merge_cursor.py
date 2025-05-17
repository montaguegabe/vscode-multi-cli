import logging

from cursor_multi.rules import cleanup_existing_imported_rules, import_cursor_rules

logger = logging.getLogger(__name__)


def main():
    logger.info("🔄 Merging Cursor rules...")

    # Clean up any previously imported rules
    logger.info("\n🔄 Cleaning up old imported rules...")
    cleanup_existing_imported_rules()

    # Import cursor rules from each repository
    logger.info("\n🔄 Importing Cursor rules...")
    import_cursor_rules()
    logger.info("\n✨ Cursor rules merged successfully!")


if __name__ == "__main__":
    main()
