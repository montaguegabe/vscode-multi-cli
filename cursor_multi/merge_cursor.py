from .rules import cleanup_existing_imported_rules, import_cursor_rules


def main():
    print("🔄 Merging Cursor rules...")

    # Clean up any previously imported rules
    print("\n🔄 Cleaning up old imported rules...")
    cleanup_existing_imported_rules()

    # Import cursor rules from each repository
    print("\n🔄 Importing Cursor rules...")
    import_cursor_rules()
    print("\n✨ Cursor rules merged successfully!")


if __name__ == "__main__":
    main()
