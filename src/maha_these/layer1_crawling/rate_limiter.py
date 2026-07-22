"""RateLimiter — limitation de débit par token bucket.

Utilisé par les crawlers pour respecter les limites des plateformes.
Implémentation simple, thread-safe, sans dépendance externe.
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Token bucket : autorise ``rate`` requêtes par ``per`` secondes."""

    def __init__(self, rate: int, per: float = 60.0, capacity: int | None = None) -> None:
        self.rate = rate
        self.per = per
        self.capacity = capacity if capacity is not None else rate
        self._tokens = float(self.capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._tokens = min(
            self.capacity, self._tokens + elapsed * (self.rate / self.per)
        )
        self._last = now

    def acquire(self, tokens: int = 1) -> None:
        """Bloque jusqu'à ce que ``tokens`` jetons soient disponibles."""
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                wait = deficit * self.per / self.rate
            time.sleep(wait)

    def try_acquire(self, tokens: int = 1) -> bool:
        """Tente d'acquérir sans bloquer ; renvoie True si accordé."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
