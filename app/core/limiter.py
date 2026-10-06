"""In-process rate limiter. Demo deployment only; not a global quota."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])
