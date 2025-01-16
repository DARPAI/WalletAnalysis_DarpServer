import asyncio
import functools
from collections.abc import Awaitable
from collections.abc import Callable
from datetime import datetime
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Type

import lib.log as logger


def retry_error(
    max_retries: int = 5, retry_delay: int = 2
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Optional[Any]]]]:
    def decorator(
        func: Callable[..., Awaitable[Any]]
    ) -> Callable[..., Awaitable[Optional[Any]]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Optional[Any]:
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries:
                        logger.info(
                            f"{func.__name__} Retrying... Attempt {attempt}/{max_retries}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.warning(
                            f"{func.__name__} Failed after {max_retries} attempts: {e}"
                        )
                        return None
            return None

        return wrapper

    return decorator


def with_logs(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    @functools.wraps(func)
    async def decorator(*args, **kwargs) -> Any:
        start_time: datetime = datetime.now()
        logger.info(f"{func.__name__} {start_time=:%Y-%m-%d %H:%M:%S}")
        result: Any = await func(*args, **kwargs)
        end_time: datetime = datetime.now()
        duration: Any = end_time - start_time
        logger.info(
            f"{func.__name__} with {result=} at {end_time=:%Y-%m-%d %H:%M:%S} with {duration=}"
        )
        return result

    return decorator


def ignore_errors(
    func: Callable[..., Awaitable[Any]],
    exception_types: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[..., Awaitable[Any]]:
    @functools.wraps(func)
    async def decorator(*args, **kwargs) -> Optional[Any]:
        try:
            return await func(*args, **kwargs)
        except exception_types as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return None

    return decorator
