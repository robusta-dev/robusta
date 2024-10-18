
import re
from typing import Dict, List

REGEXP_FIND_SELECTOR = r'\{\{\s*labels\.([^\s]+)\s*\}\}'

def resolve_selectors(labels:Dict, selectors:List[str]) -> List[str]:
    """
    Allows referencing of labels inside selectors and returns parsed selectors.

    e.g.
    labels={"my_label": "my_value"}
    resolve_selectors(labels, ["{{labels.my_label}}"]) => ["my_value"]
    """
    def replace_label(match):
        key = match.group(1).strip()
        return labels.get(key, match.string)

    resolved_selectors = [re.sub(REGEXP_FIND_SELECTOR, replace_label, selector) for selector in selectors]
    return resolved_selectors
