from typing import List

from ..model.services import ServiceInfo, get_service_key


class TopServiceResolver:

    cached_services: List[ServiceInfo] = []

    # TODO remove this guess function
    # temporary try to guess who the owner service is.
    @staticmethod
    def guess_service_key(name: str, namespace: str) -> str:
        for cached_service in TopServiceResolver.cached_services:
            if cached_service.namespace == namespace and name.startswith(
                cached_service.name
            ):
                return get_service_key(
                    cached_service.name,
                    cached_service.service_type,
                    cached_service.namespace,
                )
        return ""
