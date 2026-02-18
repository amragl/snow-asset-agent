"""Entry point: ``python -m snow_asset_agent``."""

from __future__ import annotations

import logging

from snow_asset_agent.config import get_config
from snow_asset_agent.server import mcp


def main() -> None:
    cfg = get_config()
    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    mcp.run()


if __name__ == "__main__":
    main()
