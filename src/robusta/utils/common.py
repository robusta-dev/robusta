from hikaru import DiffDetail
from typing import List


# TODO: filter out all the managed fields crap
def is_matching_diff(diff_detail: DiffDetail, fields_to_monitor: List[str]) -> bool:
    return any(
        substring in diff_detail.formatted_path for substring in fields_to_monitor
    )
