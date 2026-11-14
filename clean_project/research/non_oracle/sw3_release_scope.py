from contextvars import ContextVar
from contextlib import contextmanager
_active=ContextVar("sw3_release",default=False)
def check_scope():
    if not _active.get():
        raise PermissionError("Controlled release scope required")
@contextmanager
def _authorized_scope():
    token=_active.set(True)
    try:
        yield
    finally:
        _active.reset(token)
