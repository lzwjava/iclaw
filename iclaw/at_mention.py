import os
import re
from pathlib import Path


def resolve_at_mentions(text):
    """Extract @file references, return augmented text with file contents prepended."""
    mentions = re.findall(r"@(\S+)", text)
    if not mentions:
        return text
    parts = []
    for path in mentions:
        if os.path.isfile(path):
            try:
                contents = Path(path).read_text()
                parts.append(f'<file path="{path}">\n{contents}\n</file>')
            except OSError:
                pass
    if parts:
        return "\n".join(parts) + "\n\n" + text
    return text
