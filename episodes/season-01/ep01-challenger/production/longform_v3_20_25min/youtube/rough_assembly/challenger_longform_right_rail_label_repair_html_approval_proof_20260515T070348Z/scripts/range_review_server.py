#!/usr/bin/env python3
"""Static review server with byte-range support for native audio scrubbing."""

from __future__ import annotations

import argparse
import functools
import os
import posixpath
import shutil
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class RangeRequestHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler variant that returns 206 for valid Range requests."""

    range_start: int | None = None
    range_end: int | None = None

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            parts = urlsplit(self.path)
            if not parts.path.endswith("/"):
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                self.send_header("Location", parts.path + "/")
                self.end_headers()
                return None
            for index in ("index.html", "index.htm"):
                index_path = os.path.join(path, index)
                if os.path.isfile(index_path):
                    path = index_path
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        size = os.fstat(f.fileno()).st_size
        range_header = self.headers.get("Range")
        self.range_start = None
        self.range_end = None

        if range_header:
            parsed = self.parse_range_header(range_header, size)
            if parsed is None:
                f.close()
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return None
            start, end = parsed
            self.range_start = start
            self.range_end = end
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(size))

        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Last-Modified", self.date_time_string(os.fstat(f.fileno()).st_mtime))
        self.end_headers()
        return f

    @staticmethod
    def parse_range_header(header: str, size: int) -> tuple[int, int] | None:
        if not header.startswith("bytes="):
            return None
        spec = header.removeprefix("bytes=").split(",", 1)[0].strip()
        if "-" not in spec:
            return None
        raw_start, raw_end = spec.split("-", 1)
        try:
            if raw_start == "":
                suffix = int(raw_end)
                if suffix <= 0:
                    return None
                start = max(0, size - suffix)
                end = size - 1
            else:
                start = int(raw_start)
                end = int(raw_end) if raw_end else size - 1
        except ValueError:
            return None
        if start < 0 or end < start or start >= size:
            return None
        return start, min(end, size - 1)

    def copyfile(self, source, outputfile):
        try:
            if self.range_start is None or self.range_end is None:
                return super().copyfile(source, outputfile)
            source.seek(self.range_start)
            remaining = self.range_end - self.range_start + 1
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a static directory with HTTP byte ranges.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8818)
    parser.add_argument("--directory", default=".")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    handler = functools.partial(RangeRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {directory} on http://{args.host}:{args.port}/ with byte-range support", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
