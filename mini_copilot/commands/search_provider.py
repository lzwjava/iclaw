SEARCH_PROVIDERS = ["duckduckgo", "startpage"]


def handle_search_provider_command(search_provider):
    print(f"\nCurrent search provider: {search_provider}")
    print("Available providers:")
    for i, prov in enumerate(SEARCH_PROVIDERS, 1):
        marker = "*" if prov == search_provider else " "
        print(f"  {marker} {i}. {prov}")

    try:
        choice = input(
            "Select search provider (number, Enter to keep current): "
        ).strip()
        if choice:
            if choice.isdigit():
                n = int(choice)
                if 1 <= n <= len(SEARCH_PROVIDERS):
                    print(f"Search provider set to: {SEARCH_PROVIDERS[n - 1]}\n")
                    return SEARCH_PROVIDERS[n - 1]
                else:
                    print("Invalid selection.\n")
            else:
                print("Please enter a number.\n")
    except (EOFError, KeyboardInterrupt):
        print()

    return search_provider
