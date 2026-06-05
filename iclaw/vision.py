"""Vision support for iclaw - handle image files and clipboard."""

import base64
import os
import subprocess

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}


def is_image_file(path):
    """Check if a file is an image based on extension."""
    _, ext = os.path.splitext(path.lower())
    return ext in IMAGE_EXTENSIONS


def read_image_base64(path):
    """Read an image file and return base64 encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime_type(path):
    """Get MIME type from file extension."""
    _, ext = os.path.splitext(path.lower())
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
    }
    return mime_map.get(ext, "image/jpeg")


def get_clipboard_image():
    """Try to get image from macOS clipboard. Returns (base64, mime_type) or (None, None)."""
    try:
        # macOS: use pngpaste if available, or osascript
        result = subprocess.run(
            ["osascript", "-e", "the clipboard as «class PNGf»"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            # Parse the hex output
            hex_str = result.stdout.decode("utf-8").strip()
            # Remove the «data PNGf» wrapper
            if "«data PNGf" in hex_str:
                hex_str = hex_str.split("«data PNGf")[1].rstrip("»").strip()
                image_bytes = bytes.fromhex(hex_str)
                return base64.b64encode(image_bytes).decode("utf-8"), "image/png"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    # Try pngpaste as fallback
    try:
        result = subprocess.run(
            ["pngpaste", "-"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            return base64.b64encode(result.stdout).decode("utf-8"), "image/png"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None, None


def make_image_message(text, image_base64, mime_type="image/jpeg"):
    """Create a multimodal message with text and image."""
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
            },
        ],
    }


def resolve_at_mentions_with_vision(text):
    """Extract @file references, handle images as vision content.

    Returns (resolved_text, list_of_image_parts).
    Each image_part is {"base64": str, "mime": str, "path": str}.
    """
    import re

    mentions = re.findall(r"@(\S+)", text)
    if not mentions:
        return text, []

    from pathlib import Path

    text_parts = []
    image_parts = []

    for path in mentions:
        if os.path.isfile(path):
            if is_image_file(path):
                b64 = read_image_base64(path)
                mime = get_image_mime_type(path)
                image_parts.append({"base64": b64, "mime": mime, "path": path})
            else:
                try:
                    contents = Path(path).read_text()
                    text_parts.append(f'<file path="{path}">\n{contents}\n</file>')
                except OSError:
                    pass

    result = text
    if text_parts:
        result = "\n".join(text_parts) + "\n\n" + text
    return result, image_parts


def make_multimodal_message(text, image_parts):
    """Create a multimodal message with text and images."""
    if not image_parts:
        return {"role": "user", "content": text}

    content = []
    for img in image_parts:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{img['mime']};base64,{img['base64']}"},
            }
        )
    content.append({"type": "text", "text": text})
    return {"role": "user", "content": content}
