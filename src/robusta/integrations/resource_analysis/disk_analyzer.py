DISK_SUFFIXES = ["B", "KiB", "MiB", "GiB", "PiB"]
DISK_FACTOR = 1024


class DiskTransformer:
    @staticmethod
    def get_readable_form(num_bytes: int) -> str:
        i = 0
        while num_bytes >= DISK_FACTOR:
            num_bytes = num_bytes / DISK_FACTOR
            i += 1
        if i >= len(DISK_SUFFIXES):
            raise Exception(f"{num_bytes} is too big and cannot be converted to readable form")

        num = round(num_bytes, 2)
        suffix = DISK_SUFFIXES[i]
        return f"{num}{suffix}"
