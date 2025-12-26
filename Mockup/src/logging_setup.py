from __future__ import annotations

import logging
from rich.console import Console
from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO) -> None:
    console = Console(width=100)

    handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=False,
        markup=False,
    )

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s %(name)s:\n    %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
