from iclaw import log

LEVELS = {"verbose": log.VERBOSE, "info": log.INFO}


def handle_log_command(arg):
    if arg is None:
        print(f"Log level: {log.level_name(log.get_level())}")
        return

    if arg not in LEVELS:
        print(f"Unknown log level: {arg}. Use 'verbose' or 'info'.")
        return

    log.set_level(LEVELS[arg])
    print(f"Log level set to: {arg}")
