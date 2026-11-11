"""Marker distinguishing this app's own writes to system-managed records from user writes.

A catalog zone (RFC 9432) contains only records this app creates and maintains, so the guards on
`DNSRecord` and its queryset refuse every user write to them. The code that maintains those
records has to identify itself, and neither `full_clean()` nor `QuerySet.delete()` accepts custom
keyword arguments, so the marker travels out of band.

The flag is a `contextvars.ContextVar`, so concurrent asyncio tasks do not see each other's value.
A thread started without a copy of the context does not see it either, so work handed to a thread
pool must enter `system_write()` inside each worker.
"""

import contextlib
import contextvars

_system_write_flag = contextvars.ContextVar("nautobot_dns_models_system_write", default=False)


def system_write_in_progress():
    """Return whether the calling context is inside a `system_write()` block."""
    return _system_write_flag.get()


@contextlib.contextmanager
def system_write():
    """Mark records written inside this block as maintained by the app rather than by a user."""
    token = _system_write_flag.set(True)
    try:
        yield
    finally:
        _system_write_flag.reset(token)
