from hikaru import DiffDetail, HikaruBase
from typing import List


# TODO: filter out all the managed fields crap
def is_matching_diff(diff_detail: DiffDetail, fields_to_monitor: List[str]) -> bool:
    return any(
        substring in diff_detail.formatted_path for substring in fields_to_monitor
    )


def duplicate_without_fields(obj: HikaruBase, omitted_fields: List[str]):
    """
    Duplicate a hikaru object, omitting the specified fields

    This is useful when you want to compare two versions of an object and first "cleanup" fields that shouldn't be
    compared.

    :param HikaruBase obj: A kubernetes object
    :param List[str] omitted_fields: List of fields to be omitted. Field name format should be '.' separated
                                     For example: ["status", "metadata.generation"]
    """
    if obj is None:
        return None

    duplication = obj.dup()

    for field_name in omitted_fields:
        field_parts = field_name.split(".")
        try:
            if len(field_parts) > 1:
                parent_obj = duplication.object_at_path(field_parts[:-1])
            else:
                parent_obj = duplication

            setattr(parent_obj, field_parts[-1], None)
        except Exception:
            pass  # in case the field doesn't exist on this object

    return duplication
