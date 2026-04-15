import frappe

def run():
    """Diagnostic: check how many published articles exist and test keyword search."""
    # 1. Count published articles
    count = frappe.db.count("HD Article", {"status": "Published"})
    print(f"Total published articles: {count}")

    # 2. List all published articles
    articles = frappe.get_all(
        "HD Article",
        filters={"status": "Published"},
        fields=["name", "title", "category"],
        limit=50,
    )
    for a in articles:
        print(f"  [{a.name}] {a.title} (category={a.category})")

    # 3. Test the _search_articles function
    from helpdesk.api.ai_chat import _search_articles
    test_queries = ["helpdesk", "how", "guide", "vacuum", "pump"]
    for q in test_queries:
        results = _search_articles(q)
        titles = [r.title for r in results]
        print(f"\nSearch '{q}': {len(results)} results -> {titles}")

    # 4. Check DB charset
    charset_info = frappe.db.sql("SELECT @@character_set_database, @@collation_database", as_dict=True)
    print(f"\nDB charset: {charset_info}")

    # 5. Check the HD Article table charset
    table_info = frappe.db.sql("SHOW CREATE TABLE `tabHD Article`", as_list=True)
    if table_info:
        create_stmt = table_info[0][1]
        # Print just the last line with ENGINE/CHARSET
        for line in create_stmt.split("\n"):
            if "ENGINE" in line or "CHARSET" in line:
                print(f"Table charset: {line.strip()}")
