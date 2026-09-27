from collections.abc import Callable
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import TypeVar

from loguru import logger


Item = TypeVar('Item')


def run_concurrently(items: Iterable[Item], worker: Callable[[Item], object], workers: int, total: int, hide_progress: bool) -> None:
    """Process items sequentially or on a thread pool, logging errors per item.

    Progress callbacks count completed work while a lazy input is still being
    consumed. Keyboard interrupts cancel pending work without waiting for workers.
    """

    from tqdm import tqdm

    def safe_worker(item: Item) -> None:
        try:
            worker(item)
        except Exception as error:
            logger.error(f'Could not process {item}: {error}')

    if workers <= 1:
        for item in tqdm(items, ncols=80, position=0, leave=False, total=total, disable=hide_progress):
            safe_worker(item)
        return

    progress = tqdm(total=total, ncols=80, position=0, leave=False, disable=hide_progress)
    executor = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = []
        for item in items:
            future = executor.submit(safe_worker, item)
            future.add_done_callback(lambda completed: progress.update(1))
            futures.append(future)
        for completed in as_completed(futures):
            pass
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        progress.close()
    executor.shutdown()
