"""
app/rate_limit.py

Shared slowapi Limiter instance, keyed by client IP. 20 req/min matches the
"strict rate-limiting" spec called out in the original project doc's
Security & Privacy section, to prevent a public demo URL from being used to
run up hosting costs or degrade availability for actual judges.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)