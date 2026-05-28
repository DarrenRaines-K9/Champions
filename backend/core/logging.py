"""
Loguru configuration for Champions backend.

Call configure_logging() once at app startup (AppConfig.ready).
After that, all code imports `from loguru import logger` directly —
no per-module getLogger boilerplate.

Why this file exists:
- Django internally uses stdlib logging. InterceptHandler redirects those
  calls into Loguru so everything flows through one pipeline.
- Sentry's Django integration only captures *unhandled* exceptions. The
  custom sink below also forwards logger.exception() calls so caught errors
  still surface in Sentry.
"""

import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Route stdlib logging calls into Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _sentry_sink(message):
    """Forward ERROR+ log records to Sentry so caught exceptions are visible."""
    import sentry_sdk

    record = message.record
    if record["level"].no >= logger.level("ERROR").no:
        exception = record["exception"]
        if exception:
            sentry_sdk.capture_exception(exception.value)
        else:
            sentry_sdk.capture_message(record["message"], level="error")


def configure_logging(*, debug: bool = False, json: bool = False, sentry_dsn: str = "") -> None:
    logger.remove()

    if json:
        logger.add(
            sys.stdout,
            level="INFO",
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stderr,
            level="DEBUG" if debug else "INFO",
            colorize=True,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
            ),
            backtrace=debug,
            diagnose=debug,
        )

    if sentry_dsn:
        logger.add(_sentry_sink, level="ERROR", backtrace=False, diagnose=False)

    # Silence noisy third-party loggers.
    for noisy in ("urllib3", "asyncio", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
