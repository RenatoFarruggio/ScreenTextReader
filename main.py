from __future__ import annotations

import logging

from src.gui.app import run_app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    run_app()


if __name__ == "__main__":
    main()
