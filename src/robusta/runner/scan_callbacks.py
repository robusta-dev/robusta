import hmac
import secrets
import threading

from cachetools import TTLCache

SCAN_CALLBACK_TTL_SECONDS = 24 * 60 * 60
SCAN_CALLBACK_MAX_PENDING = 1000
# query parameter that carries the token on the URL handed to the scan job
SCAN_TOKEN_QUERY_PARAM = "scan_token"


class ScanCallbackTokens:
    """
    Tokens that let a scan job this runner started post its result back.

    The trigger endpoint accepts a result only for a scan the runner itself started, and only with the
    random token it handed to that scan's job.
    Tokens are held in memory: a scan that reports back after a runner restart is rejected.
    """

    _tokens: TTLCache = TTLCache(maxsize=SCAN_CALLBACK_MAX_PENDING, ttl=SCAN_CALLBACK_TTL_SECONDS)
    _lock = threading.Lock()

    @classmethod
    def issue(cls, scan_id: str) -> str:
        token = secrets.token_urlsafe(32)
        with cls._lock:
            cls._tokens[scan_id] = token
        return token

    @classmethod
    def is_valid(cls, scan_id: str, token: str) -> bool:
        with cls._lock:
            expected = cls._tokens.get(scan_id)
        if not expected or not token:
            return False
        return hmac.compare_digest(expected.encode(), token.encode())
