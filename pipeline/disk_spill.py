"""Opt-in, private, quota-bounded temporary disk spill for opaque bytes.

No serialization, model-specific payload processing, persistence, or silent
filesystem writes. The caller owns the disk root and explicitly enables spill.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from threading import RLock
from typing import Iterator


@dataclass(frozen=True)
class SpillRef:
    """Opaque handle; consuming code should stream chunks, not load all into RAM."""
    path: Path
    size_bytes: int
    owner: str

    def iter_chunks(self, chunk_bytes: int = 256 * 1024) -> Iterator[bytes]:
        """Read a temporary spill without loading the entire buffer in RAM.

        Valid only while the delivery callback holds this reference.
        """
        if type(chunk_bytes) is not int or chunk_bytes < 1:
            raise ValueError('chunk_bytes must be positive')
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        read = 0
        with os.fdopen(os.open(self.path, flags), 'rb') as stream:
            while True:
                chunk = stream.read(chunk_bytes)
                if not chunk:
                    break
                read += len(chunk)
                if read > self.size_bytes:
                    raise IOError('Spill data larger than declared size')
                yield chunk
        if read != self.size_bytes:
            raise IOError('Spill data truncated')


class DiskSpill:
    def __init__(self, directory: str | Path, max_disk_bytes: int,
                 min_free_bytes: int = 256 * 1024 * 1024):
        if type(max_disk_bytes) is not int or max_disk_bytes < 1:
            raise ValueError('max_disk_bytes must be positive')
        if type(min_free_bytes) is not int or min_free_bytes < 0:
            raise ValueError('min_free_bytes must be non-negative')
        raw = Path(directory)
        if raw.is_symlink() or not raw.is_dir():
            raise ValueError('Spill root must be an existing real directory')
        self.root = raw.resolve(strict=True)
        self.directory = Path(tempfile.mkdtemp(prefix='dolorain-box-', dir=self.root))
        self.directory.chmod(0o700)
        self.owner = secrets.token_hex(16)
        self.max_disk_bytes = max_disk_bytes
        self.min_free_bytes = min_free_bytes
        self.used_bytes = 0
        self.written_bytes = 0
        self._known: dict[Path, int] = {}
        self._lock = RLock()
        self._closed = False

    def __enter__(self) -> 'DiskSpill':
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    def _check(self, ref: SpillRef) -> None:
        if not isinstance(ref, SpillRef) or ref.owner != self.owner or ref.path not in self._known:
            raise ValueError('Unknown or already released spill reference')

    def put(self, payload: bytes | bytearray | memoryview) -> SpillRef:
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise TypeError('Disk spill accepts bytes-like payloads only')
        view = memoryview(payload).cast('B')
        size = view.nbytes
        with self._lock:
            if self._closed:
                raise RuntimeError('Disk spill is closed')
            if size > self.max_disk_bytes - self.used_bytes:
                raise ValueError('Disk spill quota exceeded')
            if shutil.disk_usage(self.directory).free < size + self.min_free_bytes:
                raise OSError('Insufficient free disk space for spill reserve')
            self.used_bytes += size
            path = self.directory / (secrets.token_hex(16) + '.spill')
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'wb') as out:
                    out.write(view)
                self._known[path] = size
                self.written_bytes += size
                return SpillRef(path, size, self.owner)
            except BaseException:
                path.unlink(missing_ok=True)
                self.used_bytes -= size
                raise

    def chunks(self, ref: SpillRef, chunk_bytes: int = 256 * 1024) -> Iterator[bytes]:
        if type(chunk_bytes) is not int or chunk_bytes < 1:
            raise ValueError('chunk_bytes must be positive')
        with self._lock:
            self._check(ref)
            # Prevent accidental following of a substituted file under a writable parent.
            flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
            fd = os.open(ref.path, flags)
        os.close(fd)
        yield from ref.iter_chunks(chunk_bytes)

    def release(self, ref: SpillRef) -> None:
        with self._lock:
            self._check(ref)
            ref.path.unlink()
            self.used_bytes -= self._known.pop(ref.path)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            for path in list(self._known):
                path.unlink(missing_ok=True)
            self._known.clear()
            self.used_bytes = 0
            self.directory.rmdir()
