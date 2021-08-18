def mask_secret(secret: str) -> str:
    if len(secret) > 3:
        return f"{secret[0:3]}****"
    else:
        return "*****"
