import os


def handle_proxy_command(current_proxy, arg):
    if arg is None:
        if current_proxy:
            print(f"  proxy: {current_proxy}")
        else:
            print("  proxy: (not set)")
        return current_proxy

    arg = arg.strip("\"'")

    if arg == "off":
        print("  Proxy cleared.")
        return None

    if not (arg.startswith("http://") or arg.startswith("https://")):
        print(f"  Invalid proxy URL: {arg}")
        print("  Only http:// and https:// schemes are supported.")
        return current_proxy

    print(f"  Proxy set to {arg}")
    return arg


def handle_ca_bundle_command(current_ca_bundle, arg):
    if arg is None:
        if current_ca_bundle:
            print(f"  ca_bundle: {current_ca_bundle}")
        else:
            print("  ca_bundle: (system default)")
        return current_ca_bundle

    if arg == "off":
        print("  CA bundle cleared. Using system default.")
        return None

    abs_path = os.path.abspath(arg)
    if not os.path.isfile(abs_path):
        print(f"  File not found: {abs_path}")
        return current_ca_bundle

    print(f"  CA bundle set to {abs_path}")
    return abs_path
