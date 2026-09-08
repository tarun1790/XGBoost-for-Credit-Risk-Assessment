import time
from collections import defaultdict
from typing import Dict, List, Tuple
from threading import Lock
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    Thread-safe, in-memory sliding window rate limiter.
    Limits request rates by client IP and endpoint tag.
    """
    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Evaluates whether a request with the given key is within rate limits.
        Returns (is_allowed, retry_after_seconds).
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        with self._lock:
            # Filter out timestamps outside the sliding window
            timestamps = self._requests[key]
            valid_timestamps = [t for t in timestamps if t > window_start]
            self._requests[key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                earliest_valid = valid_timestamps[0]
                retry_after = int(earliest_valid + window_seconds - current_time) + 1
                return False, max(1, retry_after)

            self._requests[key].append(current_time)
            return True, 0


class AccountLockoutManager:
    """
    Defends against automated credential stuffing and brute-force attacks.
    Tracks failed authentication attempts by username and IP.
    Initiates a progressive lockout if threshold is exceeded.
    """
    def __init__(self, max_failures: int = 5, lockout_seconds: int = 900): # 15 minutes lockout
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self._failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self._locked_until: Dict[str, float] = {}
        self._lock = Lock()

    def record_failed_attempt(self, username: str, ip: str) -> Tuple[bool, int]:
        """
        Records an authentication failure. Returns (is_now_locked, remaining_seconds).
        """
        current_time = time.time()
        key = username.lower().strip()

        with self._lock:
            # Expire attempts older than the lockout window
            attempts = [t for t in self._failed_attempts[key] if current_time - t < self.lockout_seconds]
            attempts.append(current_time)
            self._failed_attempts[key] = attempts

            if len(attempts) >= self.max_failures:
                self._locked_until[key] = current_time + self.lockout_seconds
                self._failed_attempts[key] = [] # Reset on lockout trigger
                return True, self.lockout_seconds

            return False, 0

    def is_locked_out(self, username: str) -> Tuple[bool, int]:
        """Checks if a given username is actively locked out."""
        current_time = time.time()
        key = username.lower().strip()

        with self._lock:
            if key in self._locked_until:
                lockout_end = self._locked_until[key]
                if current_time < lockout_end:
                    remaining = int(lockout_end - current_time) + 1
                    return True, remaining
                else:
                    del self._locked_until[key]

            return False, 0

    def record_successful_login(self, username: str):
        """Clears failed attempts upon legitimate authentication."""
        key = username.lower().strip()
        with self._lock:
            if key in self._failed_attempts:
                del self._failed_attempts[key]
            if key in self._locked_until:
                del self._locked_until[key]

    def get_security_telemetry(self) -> Dict[str, int]:
        """Returns active security metrics for admin monitoring."""
        current_time = time.time()
        with self._lock:
            active_locks = sum(1 for until in self._locked_until.values() if until > current_time)
            active_warning_accounts = len(self._failed_attempts)
            return {
                "active_locked_accounts": active_locks,
                "accounts_with_failed_attempts": active_warning_accounts
            }


# Singleton instances
rate_limiter = SlidingWindowRateLimiter()
lockout_manager = AccountLockoutManager(max_failures=5, lockout_seconds=900)


# FastAPI Dependencies for Rate Limiting
def get_client_ip(request: Request) -> str:
    """Extracts client IP from X-Forwarded-For or client host."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


async def rate_limit_login(request: Request):
    """Limits login endpoint to 5 attempts per 60 seconds per IP."""
    ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.is_allowed(f"login:{ip}", max_requests=5, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


async def rate_limit_register(request: Request):
    """Limits account registration to 3 accounts per 60 seconds per IP."""
    ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.is_allowed(f"register:{ip}", max_requests=3, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for user registration. Retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


async def rate_limit_computation(request: Request):
    """Throttles heavy Monte Carlo / ML assessment endpoints to 30 requests per minute per IP."""
    ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.is_allowed(f"compute:{ip}", max_requests=30, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"High-frequency computation limit reached. Retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
