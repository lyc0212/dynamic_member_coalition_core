"""Bounded JSON framing shared by IPC workers and the nonblocking guardian.

There are no scientific, process-management, or private-input dependencies.
"""
from collections import deque
import json
import selectors
import socket
import struct
import time

from .common import MAX_FRAME, IO_CHUNK, POLL, ContractError


def encode(message):
    if not isinstance(message, dict):
        raise ContractError('IPC top level must be an object')
    raw = json.dumps(message, ensure_ascii=False, allow_nan=False,
                     separators=(',', ':')).encode('utf-8')
    if not 0 < len(raw) <= MAX_FRAME:
        raise ContractError('IPC frame size outside frozen bounds')
    return struct.pack('!I', len(raw)) + raw


def _reject_constant(value):
    raise ContractError('Nonfinite JSON token: ' + value)


class Peer:
    """One nonblocking socket; each read/write syscall is at most 64 KiB."""
    def __init__(self, sock, *, partial_timeout=10.0):
        self.socket = sock
        self.socket.setblocking(False)
        self.incoming = bytearray()
        self.expected = None
        self.partial_started = None
        self.partial_timeout = float(partial_timeout)
        self.outgoing = deque()
        self.out_offset = 0
        self.queued_bytes = 0
        self.max_queued_bytes = 0
        self.eof = False
        self.bytes_received = self.bytes_sent = 0

    def queue(self, message):
        self.queue_bytes(encode(message))

    def queue_bytes(self, raw):
        """Raw enqueue is used only by fixed malformed-framing probes."""
        if self.queued_bytes + len(raw) > 4 * MAX_FRAME:
            raise ContractError('Bounded IPC output queue exceeded')
        self.outgoing.append(bytes(raw))
        self.queued_bytes += len(raw)
        self.max_queued_bytes = max(self.max_queued_bytes, self.queued_bytes)

    def write_ready(self):
        if not self.outgoing:
            return 0
        head = self.outgoing[0]
        try:
            count = self.socket.send(memoryview(head)[self.out_offset:self.out_offset + IO_CHUNK])
        except (BlockingIOError, InterruptedError):
            return 0
        if count == 0:
            raise EOFError('Peer stopped accepting queued bytes')
        self.out_offset += count
        self.queued_bytes -= count
        self.bytes_sent += count
        if self.out_offset == len(head):
            self.outgoing.popleft()
            self.out_offset = 0
        return count

    def _extract(self, now):
        messages = []
        while True:
            if self.expected is None:
                if len(self.incoming) < 4:
                    break
                self.expected = struct.unpack('!I', self.incoming[:4])[0]
                del self.incoming[:4]
                if not 0 < self.expected <= MAX_FRAME:
                    raise ContractError('Invalid incoming IPC frame length')
            if len(self.incoming) < self.expected:
                break
            raw = bytes(self.incoming[:self.expected])
            del self.incoming[:self.expected]
            self.expected = None
            try:
                value = json.loads(raw.decode('utf-8'), parse_constant=_reject_constant)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ContractError('Invalid UTF-8/JSON IPC payload') from error
            if not isinstance(value, dict):
                raise ContractError('IPC top level must be an object')
            messages.append(value)
            # A next partial frame starts with its own first observed bytes.
            self.partial_started = now if self.incoming else None
        return messages

    def read_ready(self, now=None):
        now = time.monotonic() if now is None else now
        try:
            raw = self.socket.recv(IO_CHUNK)
        except (BlockingIOError, InterruptedError):
            return []
        if not raw:
            self.eof = True
            if self.incoming or self.expected is not None:
                raise EOFError('EOF with an incomplete IPC frame')
            return []
        if self.partial_started is None:
            self.partial_started = now
        self.incoming.extend(raw)
        self.bytes_received += len(raw)
        return self._extract(now)

    def check_partial_deadline(self, now=None):
        now = time.monotonic() if now is None else now
        if self.partial_started is not None and now >= self.partial_started + self.partial_timeout:
            raise TimeoutError('IPC partial-frame assembly deadline')

    def close(self):
        self.socket.close()


class WireClient:
    """Synchronous worker helper with bounded waits and preserved partial reads.

    recv(timeout=...) raises TimeoutError without discarding partial data.
    send timeout is fatal to that logical message; callers must stop the job.
    ``socket`` is exposed only for predeclared synthetic framing probes.
    """
    def __init__(self, fd, *, partial_timeout=10.0):
        # The guardian created an AF_UNIX socketpair. Explicit metadata avoids
        # probing an inherited descriptor with network-family discovery calls.
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0, fileno=int(fd))
        self.peer = Peer(self.socket, partial_timeout=partial_timeout)
        self.messages = deque()

    def _wait(self, events, until):
        remaining = until - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('IPC operation deadline')
        with selectors.DefaultSelector() as selector:
            selector.register(self.socket, events)
            return selector.select(min(POLL, remaining))

    def send(self, message, timeout=10.0):
        until = time.monotonic() + float(timeout)
        self.peer.queue(message)
        while self.peer.outgoing:
            if self._wait(selectors.EVENT_WRITE, until):
                self.peer.write_ready()

    def recv(self, timeout=10.0):
        until = time.monotonic() + float(timeout)
        while not self.messages:
            self.peer.check_partial_deadline()
            if self.peer.eof:
                raise EOFError('IPC peer closed')
            if self._wait(selectors.EVENT_READ, until):
                self.messages.extend(self.peer.read_ready())
        return self.messages.popleft()

    def close(self):
        self.peer.close()
