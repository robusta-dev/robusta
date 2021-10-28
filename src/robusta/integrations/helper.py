def exact_match(expected, field_value) -> bool:
    if expected is None:
        return True

    return expected == field_value


def prefix_match(prefix: str, field_value: str) -> bool:
    if not prefix:
        return True

    if field_value is None:
        # we have a prefix requirement, but field doesn't exist. no match
        return False

    return field_value.startswith(prefix)
