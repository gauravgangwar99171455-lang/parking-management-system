"""
ParkSmart Pro — Logging Utility
TQM Quality Attribute: Observability & Accountability (ISO/IEC 25010)
"""

import logging
import sys
from config import LOG_FILE

_logger = None

def get_logger(name: str = "parksmart") -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger.getChild(name)

    logger = logging.getLogger("parksmart")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        try:
            fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"Warning: Could not open log file: {e}", file=sys.stderr)

        # Console Stream Handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    _logger = logger
    return logger.getChild(name)
