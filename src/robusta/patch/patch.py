import inspect
import logging
import traceback
from dataclasses import InitVar, is_dataclass
from inspect import getmodule, signature
from typing import Dict, List, Optional, Union, get_type_hints

import kubernetes.client.models
from hikaru import HikaruBase, HikaruDocumentBase
from kubernetes.client.configuration import Configuration
from kubernetes.client.models.events_v1_event import EventsV1Event
from kubernetes.client.models.v1_pod_failure_policy_rule import V1PodFailurePolicyRule
from ruamel.yaml import YAML

try:
    from typing import get_args, get_origin
except ImportError:  # pragma: no cover

    def get_args(tp):
        return tp.__args__ if hasattr(tp, "__args__") else ()

    def get_origin(tp):
        return tp.__origin__ if hasattr(tp, "__origin__") else None


NoneType = type(None)

monkey_patches_applied = False


def create_monkey_patches():
    global monkey_patches_applied
    if monkey_patches_applied:
        return
    # The 2 patched Hikaru methods are very expensive CPU wise. We patched them, and using cached attributes
    # on the hikaru class, so that we perform the expensive procedure only once
    logging.info("Creating hikaru monkey patches")
    HikaruBase.get_empty_instance = get_empty_instance
    HikaruBase._get_hints = _get_hints
    # The YAML method below is searching the file system for plugins, each time a parser is created
    # We create many parser, and this is very inefficient.
    # The plugins doesn't change during program execution.
    # We added caching to search for the plugins only once
    logging.info("Creating yaml monkey patch")
    YAML.official_plug_ins = official_plug_ins
    # The patched method is due to a bug in containerd that allows for containerImages to have no names
    # which causes the kubernetes python api to throw an exception
    logging.info("Creating kubernetes ContainerImage monkey patch")
    EventsV1Event.event_time = EventsV1Event.event_time.setter(event_time)
    patch_on_pod_conditions()
    monkey_patches_applied = True
    patch_kubernetes_models()


def patch_on_pod_conditions():
    # This fixes https://github.com/kubernetes-client/python/issues/2056 before the
    # k8s people take care of it (it's urgent for us).

    logging.debug("Creating kubernetes PodFailurePolicyRUle.on_pod_conditions monkey patch")

    def patched_setter(self, on_pod_conditions):
        self._on_pod_conditions = on_pod_conditions

    V1PodFailurePolicyRule.on_pod_conditions = V1PodFailurePolicyRule.on_pod_conditions.setter(patched_setter)


def patch_kubernetes_models():
    """
    See https://github.com/kubernetes-client/python/issues/1921 and https://github.com/tomplus/kubernetes_asyncio/issues/247
    Fix based on files at end of https://github.com/tomplus/kubernetes_asyncio/pull/300/files
    """
    # add get_default to kubernetes Configuration
    setattr(Configuration, 'get_default', classmethod(get_default))

    # Loop over all model classes in the kubernetes.client.models package
    for name, obj in inspect.getmembers(kubernetes.client.models):
        if inspect.isclass(obj):  # Check if the object is a class
            # Get the class source code as a string
            source_code = inspect.getsource(obj)
            if 'local_vars_configuration = Configuration.get_default_copy()' in source_code:
                # Monkey patching: Replace Configuration() with Configuration.get_default()
                obj.local_vars_configuration = Configuration.get_default()
            # Check if the pattern is present
            if 'local_vars_configuration = Configuration()' in source_code:
                # Monkey patching: Replace Configuration() with Configuration.get_default()
                obj.local_vars_configuration = Configuration.get_default()


def get_default(cls):
    """Get default instance of configuration.

    :return: The Configuration object.
    """
    logging.debug("get_default patch called")
    if cls._default is None:
        cls.set_default(Configuration())
    return cls._default


def event_time(self, event_time):
    self._event_time = event_time


def official_plug_ins(self):
    return []


# hikaru meta.py monkey patch function
@classmethod
def get_empty_instance(cls):
    """
    Returns a properly initialized instance with Nones and empty collections

    :return: and instance of 'cls' with all scalar attrs set to None and
        all collection attrs set to an appropriate empty collection
    """
    kw_args = {}
    # The 3 lines below are added, to use cached arguments to create the empty class instance
    cached_args = getattr(cls, "cached_args", None)
    if cached_args:
        return cls(**cached_args)
    sig = signature(cls.__init__)
    init_var_hints = {k for k, v in get_type_hints(cls).items() if isinstance(v, InitVar) or v is InitVar}
    hints = cls._get_hints()
    for p in sig.parameters.values():
        if p.name in ("self", "client") or p.name in init_var_hints:
            continue
        # skip these either of these next two since they are supplied by default,
        # but only if they have default values
        if p.name in ("apiVersion", "kind"):
            if issubclass(cls, HikaruDocumentBase):
                continue
        f = hints[p.name]
        initial_type = f
        origin = get_origin(initial_type)
        is_required = True
        if origin is Union:
            type_args = get_args(f)
            initial_type = type_args[0]
            is_required = False
        if (
            (type(initial_type) == type and issubclass(initial_type, (int, str, bool, float)))
            or (is_dataclass(initial_type) and issubclass(initial_type, HikaruBase))
            or initial_type is object
        ):
            # this is a type that might default to None
            # kw_args[p.name] = None
            if is_required:
                if is_dataclass(initial_type) and issubclass(initial_type, HikaruBase):
                    kw_args[p.name] = initial_type.get_empty_instance()
                else:
                    kw_args[p.name] = ""
            else:
                kw_args[p.name] = None
        else:
            origin = get_origin(initial_type)
            if origin in (list, List):
                # ok, just stuffing an empty list in here can be a problem,
                # as we don't know if this is going to then be put through
                # get clean dict; if it's required, a clean dict will remove
                # the list. So we need to put something inside this list so it
                # doesn't get blown away. But ONLY if it's required
                if is_required:
                    list_of_type = get_args(initial_type)[0]
                    if issubclass(list_of_type, HikaruBase):
                        kw_args[p.name] = [list_of_type.get_empty_instance()]
                    else:
                        kw_args[p.name] = [None]
                else:
                    kw_args[p.name] = []
            elif origin in (dict, Dict):
                kw_args[p.name] = {}
            else:
                raise NotImplementedError(
                    f"Internal error! Unknown type"
                    f" {initial_type}"
                    f" for parameter {p.name} in"
                    f" {cls.__name__}. Please file a"
                    f" bug report."
                )  # pragma: no cover
    new_inst = cls(**kw_args)
    # Caching the empty instance creation args, to use next time we want to create an empty instance
    cls.cached_args = kw_args
    return new_inst


@classmethod
def _get_hints(cls) -> dict:
    # The 3 lines below are added, to use cached hints
    cached_hints = getattr(cls, "cached_hints", None)
    if cached_hints:
        return cached_hints
    mro = cls.mro()
    mro.reverse()
    hints = {}
    globs = vars(getmodule(cls))
    for c in mro:
        if is_dataclass(c):
            hints.update(get_type_hints(c, globs))
    # patching ContainerImage hint to allow the names to be None due to containerd bug
    if cls.__name__ == "Event":
        hints["eventTime"] = Optional[str]
    # Caching the class hints for later use
    cls.cached_hints = hints
    return hints
