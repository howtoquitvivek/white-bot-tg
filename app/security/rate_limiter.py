"""In-memory rate limiter for login attempts."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import threading
from typing import Dict, List


class LoginRateLimiter:
    """Tracks failed login attempts to prevent brute-force attacks."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300) -> None:
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        self._failures: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_rate_limited(self, key: str) -> bool:
        """Check if a given key (e.g. IP or username) has exceeded max failed attempts."""
        now = datetime.now(timezone.utc)
        cutoff = now - self.window

        with self._lock:
            # Purge timestamps outside the window
            attempts = [ts for ts in self._failures[key] if ts > cutoff]
            self._failures[key] = attempts
            return len(attempts) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        """Record a failed login attempt for a key."""
        now = datetime.now(timezone.utc)
        with self._lock:
            self._failures[key].append(now)

    def reset(self, key: str) -> None:
        """Clear failed attempts for a key upon successful authentication."""
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        """Clear all rate limit records (useful for testing)."""
        with self._lock:
            self._failures.clear()


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=300)

