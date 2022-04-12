import asyncio

from typing import Awaitable, Callable

def sync_to_async(func) -> Callable:
    def wraps(*args) -> Awaitable:
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        return loop.run_in_executor(None, func, *args)
    return wraps