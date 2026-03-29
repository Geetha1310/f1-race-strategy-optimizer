"""
Unified Logging Configuration Module for the F1 Race Strategy Engine.

This module provides centralized logging setup and management for all backend
components including routes, simulation engines, and model inference layers.
Ensures consistent, formatted log output across the entire application with
environment-based configuration and no duplicate handler pollution.
"""

import logging
import os
from datetime import datetime

# ============================================================================
# LOG FORMAT CONFIGURATION
# ============================================================================

LOG_FORMAT: str = "[%(asctime)s] [%(levelname)-8s] [%(name)s] — %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# CORE LOGGER FUNCTION
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a configured logger instance for a given module name.

    Initializes a logger with consistent formatting and console output.
    Prevents duplicate handlers by checking existing handler count.
    Log level is controlled via the LOG_LEVEL environment variable.

    Args:
        name: Logger identifier, typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance ready for use throughout the module.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Engine initialized.")
    """
    # --- Get or create logger --- #
    logger = logging.getLogger(name)

    # --- Retrieve log level from environment with fallback --- #
    log_level_str: str = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level_str, logging.INFO))

    # --- Prevent duplicate handler attachment --- #
    if not logger.handlers:
        # --- Create console stream handler --- #
        handler = logging.StreamHandler()

        # --- Create formatter with custom format and date format --- #
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        handler.setFormatter(formatter)

        # --- Add handler to logger --- #
        logger.addHandler(handler)

    # --- Disable propagation to prevent duplicate log bubbling --- #
    logger.propagate = False

    return logger


# ============================================================================
# STARTUP BANNER FUNCTION
# ============================================================================

def log_startup_banner() -> None:
    """
    Log the F1 Race Strategy Engine startup banner with system information.

    Displays version, configured log level, and current timestamp.
    Provides visual confirmation that the engine is starting up properly.
    Should be called once during application initialization.
    """
    engine_logger = get_logger("F1.Engine")

    # --- Retrieve current log level for display --- #
    log_level_str: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # --- Get current formatted timestamp --- #
    current_time: str = datetime.now().strftime(DATE_FORMAT)

    # --- Log startup banner --- #
    engine_logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    engine_logger.info("🏎️   F1 Race Strategy Engine — SYSTEMS ONLINE")
    engine_logger.info("    Version  : 1.0.0")
    engine_logger.info(f"    Log Level: {log_level_str}")
    engine_logger.info(f"    Time     : {current_time}")
    engine_logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

# To use the logger in any backend module:
#
#   from logger import get_logger
#   logger = get_logger(__name__)
#
#   logger.info("Strategy engine initialised.")
#   logger.warning("Model path not found.")
#   logger.error("Simulation failed for track: Monaco")
#
# To display startup banner during app initialization:
#
#   from logger import log_startup_banner
#   log_startup_banner()
