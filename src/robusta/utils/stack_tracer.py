import faulthandler
import logging
import tempfile
import time


class StackTracer:
    @staticmethod
    def dump(traces: int = 5, sleep_duration: float = 0.5, all_threads: bool = True):
        for i in range(traces):
            try:
                logging.info(f"dump {i}")
                logging.info(StackTracer.get_traceback(all_threads))
                time.sleep(sleep_duration)
            except Exception:
                logging.error("Failed to dump threads", exc_info=True)

        logging.info(f"Finished {traces} dumps")

    @staticmethod
    def get_traceback(all_threads: bool):
        with tempfile.TemporaryFile() as tmp:
            faulthandler.dump_traceback(file=tmp, all_threads=all_threads)
            tmp.seek(0)
            return tmp.read().decode("utf-8")
