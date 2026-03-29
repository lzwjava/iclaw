INFO = 0
VERBOSE = 1

_level = VERBOSE


def set_level(level):
    global _level
    _level = level


def get_level():
    return _level


def log_info(message):
    print(message)


def log_verbose(message):
    if _level >= VERBOSE:
        print(message)


def level_name(level):
    if level == INFO:
        return "info"
    else:
        return "verbose"
