"""Bounds and origin checks for anonymous demo requests."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

MAX_BODY_BYTES = 65536


class RequestRejected(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


def read_form(header, read, host: str):
    """Read one URL-encoded form. header(name) returns a string or None."""
    origin = header("Origin")
    if origin:
        origin_host = urlparse(origin).netloc
        if origin_host and origin_host != host:
            raise RequestRejected(403, "Cross-origin request refused.")
    content_type = (header("Content-Type") or "").split(";", 1)[0].strip().lower()
    if content_type and content_type != "application/x-www-form-urlencoded":
        raise RequestRejected(415, "Unsupported content type.")
    raw_length = header("Content-Length")
    if raw_length is None or raw_length == "":
        length = 0
    else:
        try:
            length = int(raw_length)
        except ValueError:
            raise RequestRejected(400, "Invalid content length.")
    if length < 0:
        raise RequestRejected(400, "Invalid content length.")
    if length > MAX_BODY_BYTES:
        raise RequestRejected(413, "Request body is too large.")
    body = read(length) if length else b""
    if len(body) > MAX_BODY_BYTES:
        raise RequestRejected(413, "Request body is too large.")
    try:
        text = body.decode("utf-8")
    except UnicodeError:
        raise RequestRejected(400, "Request body must be UTF-8.")
    return parse_qs(text)
