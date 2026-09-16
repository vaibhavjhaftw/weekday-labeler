#!/usr/bin/env python3
"""Static server that answers byte-range requests.

python3 -m http.server answers 200 with the whole file however small a slice was
asked for, so a <video> served by it cannot be seeked -- it rewinds to whatever
happens to be buffered. Anything that serves video needs 206, so this adds it.
"""
import http.server, os, re, socketserver, sys

RANGE = re.compile(r"bytes=(\d*)-(\d*)")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        # So a page served from anywhere can read these pixels into a canvas.
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def send_head(self):
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404)
            return None
        size = os.fstat(f.fileno()).st_size
        m = RANGE.match(rng.strip())
        if not m:
            f.close()
            self.send_error(400)
            return None
        lo, hi = m.group(1), m.group(2)
        if lo == "":                                  # suffix form: bytes=-500
            length = int(hi or 0)
            start, end = max(0, size - length), size - 1
        else:
            start = int(lo)
            end = int(hi) if hi else size - 1
        end = min(end, size - 1)
        if start > end or start >= size:
            f.close()
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        f.seek(start)
        return _Slice(f, end - start + 1)


class _Slice:
    """copyfile() reads until EOF, so cap the file at the slice length."""

    def __init__(self, f, n):
        self.f, self.left = f, n

    def read(self, n=-1):
        if self.left <= 0:
            return b""
        if n < 0 or n > self.left:
            n = self.left
        b = self.f.read(n)
        self.left -= len(b)
        return b

    def close(self):
        self.f.close()


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with Server(("127.0.0.1", port), Handler) as srv:
        print(f"serving {os.getcwd()} on http://localhost:{port}")
        srv.serve_forever()
