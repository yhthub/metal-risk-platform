"""One shared worker slot for memory-heavy table parsing and transformation."""
import threading


class TableProcessingBusy(ValueError):
    """Another table job is still running; callers must not replay the request."""


_table_capacity = threading.BoundedSemaphore(1)


def run_table_processing(function, *args):
    # Acquire AND release in the worker. Cancellation of its awaiting request
    # must not advertise free capacity while pandas/openpyxl is still running.
    if not _table_capacity.acquire(blocking=False):
        raise TableProcessingBusy("另一份群体数据或清洗任务正在处理，请稍后再试。")
    try:
        return function(*args)
    finally:
        _table_capacity.release()
