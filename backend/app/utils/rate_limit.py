import hashlib
import time
from collections import defaultdict
from typing import DefaultDict, List


AUTH_RATE_LIMIT_MAX_ATTEMPTS = 5
AUTH_RATE_LIMIT_WINDOW_SECONDS = 60


class SoftRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: DefaultDict[str, List[float]] = defaultdict(list)

    def _prune(self, key: str, now: float) -> List[float]:
        """Remove expired attempts for the given key in-place."""
        cutoff = now - self.window_seconds
        attempts = [ts for ts in self._attempts.get(key, []) if ts >= cutoff]
        if attempts:
            self._attempts[key] = attempts
        else:
            self._attempts.pop(key, None)
        return attempts

    def is_limited(self, key: str, now: float | None = None) -> bool:
        current = now or time.time()
        attempts = self._prune(key, current)
        return len(attempts) >= self.max_attempts

    def record_failure(self, key: str, now: float | None = None) -> None:
        current = now or time.time()
        attempts = self._prune(key, current)
        attempts.append(current)
        self._attempts[key] = attempts

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)

    def clear(self) -> None:
        self._attempts.clear()


def make_key(scope: str, ip: str, identifier: str) -> str:
    if not identifier:
        raise ValueError("identifier is required for rate limiting")
    identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()
    identifier_component = identifier_hash[:32]
    if ip:
        ip_component = ip
    else:
        ip_component = f"unknown-ip-{identifier_hash[:8]}"
    return f"{scope}:{ip_component}:{identifier_component}"


auth_rate_limiter = SoftRateLimiter(
    max_attempts=AUTH_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)
