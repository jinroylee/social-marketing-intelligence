"""Parse supplied references without treating them as observed evidence."""

from urllib.parse import urlsplit, unquote

from .contracts import SourceReference


def parse_reference(value: str) -> SourceReference:
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or (parsed.hostname or "").lower() not in {
        "tiktok.com", "www.tiktok.com", "m.tiktok.com"
    }:
        return SourceReference(original=value)
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 3 or not parts[0].startswith("@") or parts[1] != "video":
        return SourceReference(original=value, platform="tiktok")
    handle = unquote(parts[0][1:])
    video_id = parts[2]
    if not handle or not video_id.isascii() or not video_id.isdecimal():
        return SourceReference(original=value, platform="tiktok")
    return SourceReference(value, "tiktok", "video", video_id, handle)
