from abc import ABC, abstractmethod
from cachetools import TTLCache
from threading import Lock
from typing import Optional
import logging

from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal
from robusta.api import ActionException, Action
from robusta.api import ErrorCodes


ACCOUNT_TYPE_CACHE_TIMEOUT = 900 
ACCOUNT_CACHE_SIZE = 5000


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, account_id: str) -> None:
        """
        Validate specific condition
        Raises ActionException if validation fails
        """
        pass
    
    @abstractmethod
    def is_applicable(self, action: Action) -> bool:
        pass


class AccountTypeValidator(BaseValidator):
    APPLICABLE_ACTIONS = (
        "ask_holmes",
        "holmes_workload_health",
        "holmes_conversation",
        "delayed_health_check",
        "holmes_issue_chat",
        "holmes_chat"
    )
    def __init__(self, dal: Optional[SupabaseDal]):
        self._dal = dal
        self.account_cache = TTLCache(
            maxsize=ACCOUNT_CACHE_SIZE, 
            ttl=ACCOUNT_TYPE_CACHE_TIMEOUT
        )
        self.account_cache_lock = Lock()

    def _is_account_free(self, account_id: str) -> Optional[bool]:
        try:
            if account_id in self.account_cache:
                return self.account_cache[account_id]

            if not self._dal:
                return None

            is_free = self._dal.is_account_free()
            if is_free is None:
                return None
            
            with self.account_cache_lock:
                self.account_cache[account_id] = is_free

            return is_free
        except Exception:
            logging.exception(
                f"Exception getting account status for account_id: {account_id}",
                exc_info=True
            )
            return None
        
    def is_applicable(self, action: Action) -> bool:
        return action.action_name in self.APPLICABLE_ACTIONS

    def validate(self, account_id: str) -> None:
        is_free = self._is_account_free(account_id)
        
        if is_free is None:
            raise ActionException(
                ErrorCodes.HOLMES_UNEXPECTED_ERROR,
                "Failed to validate account status"
            )
        
        if is_free:
            raise ActionException(
                ErrorCodes.HOLMES_REQUEST_ERROR,
                "This feature is not available in free accounts"
            )
