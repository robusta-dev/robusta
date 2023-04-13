

from enum import Enum
import re
from typing import Any, Dict, Iterable, List, Sequence, Set


class ObjectTraverser:
    """
    ObjectTraverser converts any object and its internals recursively 
    to a safe dictinary which can be easily converted to json or yaml
    """

    class __SkipException(Exception):
        """ __Skip internal exception used internally to skip some types"""
        pass

    def __init__(self,
                 exclude_types: List[type] = [],
                 exclude_patterns: List[str] = [],
                 exclude_empty_parent=True):
        """
        exclude_types - list of types to exclude 
        exclude_patterns - list of regex paterns to exclude
        exclude_empty_parent - drop whole parent object if all its childrens where excluded
        """
        self.exclude_types = tuple(exclude_types)
        self.exclude_empty_parent = exclude_empty_parent,
        # TODO: using jsonpath may simplify the way it works
        self.exclude_regxs = [re.compile(pattern) for pattern in exclude_patterns]

    def to_dictionary(self, obj: Any) -> Dict[str, Any]:
        """Traverses object and creates dictionary"""
        return self.__map_value(obj, path="")

    def __map_dict(self, dict: Dict, path):
        res = {}
        skipped = False
        # run over the object tiems and try to map each value through _map_value
        for key, value in dict.items():
            try:
                res[key] = self.__map_value(value, path=path + "." + key)
            except self.__SkipException:
                # just skip this key, value
                skipped = True
        # skip if the object is empty (because of its values where skipped)
        if self.exclude_empty_parent and skipped and not res:
            raise self.__SkipException
        return res

    def __map_sequence(self, seq: Iterable, path):
        res = []
        skipped = False
        # run over sequence and try to map each value through _map_value
        for index, value in enumerate(seq):
            try:
                res.append(self.__map_value(value, path=path + "." + str(index)))
            except self.__SkipException:
                # this value has to be skipped, dont add it to result
                skipped = True

        # if skipped was only the value and the list is empty, raise to skip the whole list
        if self.exclude_empty_parent and skipped and not res:
            raise self.__SkipException
        return res

    def __map_value(self, obj: Any, path) -> Dict[str, Any]:
        # handle types in the skip list
        if isinstance(obj, self.exclude_types):
            raise self.__SkipException
        if any(regx.match(path) for regx in self.exclude_regxs):
            raise self.__SkipException

        # different cases of object mapping
        if obj is None:
            return None
        if isinstance(obj, bytes):
            return str(obj)  # may depend on parsing params in future
        if isinstance(obj, (int, str, float, bool)):
            return obj
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, Dict):  # it is dictionary already
            return self.__map_dict(obj, path)
        elif isinstance(obj, (Sequence, Set)):  # list, tuple, (but not bytes and str) etc
            return self.__map_sequence(obj, path)
        elif hasattr(obj, "__dict__"):  # any class convertable to dict
            return self.__map_dict(vars(obj), path)
        else:
            return str(obj)
