import functools
import logging
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from traceback import format_exc
from typing import Any
from typing import Optional
from typing import Union

logger: "Logger"
debug: Callable[[Any], None]
info: Callable[[Any], None]
warning: Callable[[Any], None]
error: Callable[[Any], None]
exception: Callable[[Any], None]


class ModuleLogFilter(logging.Filter):
    def __init__(self, module_name: str) -> None:
        super(ModuleLogFilter, self).__init__(f"{module_name}_filter")
        self.module_name = module_name

    def filter(self, rec: logging.LogRecord) -> bool:
        return self.module_name == rec.module


class Logger(logging.Logger):
    info_log_path: Optional[str]

    def __init__(
        self,
        name: Optional[str] = None,
        level: Union[str, int] = logging.INFO,
        log_dir: Union[None, str, Path] = None,
    ) -> None:
        if name is None:
            name = "project_logger"
        if isinstance(level, str):
            level = logging.getLevelName(level)
        super().__init__(name, level)
        if log_dir is None:
            prefix_dir = Path.cwd() / "logs"
            log_suffix = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            log_dir = prefix_dir / log_suffix
            last_link = prefix_dir / "last"
            if os.name != "nt":
                last_link.unlink(missing_ok=True)
                last_link.symlink_to(log_suffix, target_is_directory=True)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.fmt = logging.Formatter(
            "%(asctime)s [%(filename)s:%(funcName)s():%(lineno)s] - %(message)s",
            "%H:%M:%S",
        )

        self.setLevel(level)
        self.add_file_handler(logging.DEBUG)
        self.add_file_handler(logging.INFO)
        self.add_file_handler(logging.WARNING)
        self.add_file_handler(logging.ERROR)
        self.addHandler(self.create_stderr_handler(logging.ERROR))

    def add_file_handler(self, level: int) -> None:
        if self.level <= level:
            log_path = Path(f"{self.log_dir}/{logging.getLevelName(level).lower()}.log")
            if level == logging.INFO:
                setattr(self, "info_log_path", log_path)
            log_handler = self.create_file_handler(log_path, level)
            self.addHandler(log_handler)

    @classmethod
    def start(
        cls,
        name: Optional[str] = None,
        level: Union[str, int] = logging.INFO,
        log_dir: Union[None, str, Path] = None,
    ) -> None:
        globals()["logger"] = logger = cls(name, level, log_dir)
        globals()["debug"] = logger.debug
        globals()["info"] = logger.info
        globals()["warning"] = logger.warning
        globals()["error"] = logger.error
        globals()["exception"] = logger.exception

    def create_file_handler(self, path: Path, level: int) -> logging.Handler:
        handler = logging.FileHandler(path, "a", encoding="utf-8")
        handler.setFormatter(self.fmt)
        handler.setLevel(level)
        return handler

    def create_stderr_handler(self, level: int) -> logging.Handler:
        handler = logging.StreamHandler()
        handler.setFormatter(self.fmt)
        handler.setLevel(level)
        return handler

    def make_logger(self, name: str, level=logging.DEBUG) -> None:
        last_name = name.split(".")[-1]
        path = Path(f"{self.log_dir}/{last_name}.log")
        handler = self.create_file_handler(path, level)
        handler.addFilter(ModuleLogFilter(last_name))
        self.addHandler(handler)

    def debug(self, msg: object, *args: Any, **kwargs: Any) -> None:
        super().debug(msg, stacklevel=2, *args, **kwargs)

    def info(self, msg: object, *args: Any, **kwargs: Any) -> None:
        super().info(msg, stacklevel=2, *args, **kwargs)

    def warning(self, msg: object, *args: Any, **kwargs: Any) -> None:
        super().warning(msg, stacklevel=2, *args, **kwargs)

    def error(self, msg: object, *args: Any, **kwargs: Any) -> None:
        super().error(msg, stacklevel=2, *args, **kwargs)

    def print(self, *args: Any) -> None:
        super().debug(str(" ".join([str(x) for x in args])), stacklevel=3)


def with_log_exception(method: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(method)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger()
        try:
            return method(*args, **kwargs)
        except Exception:
            for line in "".join(format_exc()).split("\n"):
                logger.error(line)
            raise

    return wrapped
