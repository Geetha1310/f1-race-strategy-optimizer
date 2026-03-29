"""
Centralized Configuration Module for the F1 Race Strategy Engine.

This module serves as the single source of truth for all configuration parameters,
loading environment variables via python-dotenv with safe fallback defaults.
All configuration is defined at the module level through the Config class,
enabling easy access across the application backend.
"""

import os
import logging
from dotenv import load_dotenv

# --- Load environment variables --- #
load_dotenv()

# --- Logger initialization --- #
logger = logging.getLogger(__name__)


class Config:
    """
    Centralized configuration class for the F1 Race Strategy Engine.

    All attributes are defined at the class level with environment variable
    overrides and sensible defaults. No instantiation required.
    """

    # --- Server Configuration --- #
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", 5000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # --- Model Configuration --- #
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/saved_models")
    LAP_TIME_MODEL: str = os.path.join(MODEL_PATH, "lap_time_model.pkl")
    TYRE_DEG_MODEL: str = os.path.join(MODEL_PATH, "tyre_deg_model.pkl")
    SAFETY_CAR_MODEL: str = os.path.join(MODEL_PATH, "safety_car_model.pkl")

    # --- Simulation Parameters --- #
    DEFAULT_PIT_TIME_LOSS: int = int(os.getenv("DEFAULT_PIT_TIME_LOSS", 22))
    MAX_RACE_LAPS: int = int(os.getenv("MAX_RACE_LAPS", 78))
    TYRE_COMPOUNDS: list = ["Soft", "Medium", "Hard", "Intermediate", "Wet"]
    SUPPORTED_CIRCUITS: list = ["Monaco", "Silverstone", "Monza", "Spa", "Suzuka"]

    # --- API Metadata --- #
    ENGINE_NAME: str = "F1 Race Strategy Engine"
    ENGINE_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"


def validate_config() -> None:
    """
    Validate critical configuration parameters at application startup.

    Checks model path existence and logs appropriate status messages.
    Warnings are logged if critical resources are missing, but execution
    continues to allow for graceful handling or model training.
    """
    if not os.path.exists(Config.MODEL_PATH):
        logger.warning(
            f"⚠️  Model path not found: {Config.MODEL_PATH}. "
            f"Ensure models are trained before running."
        )
    else:
        logger.info(
            f"✅  Config loaded. Engine: {Config.ENGINE_NAME} v{Config.ENGINE_VERSION} "
            f"| Port: {Config.SERVER_PORT}"
        )


# --- Startup validation --- #
validate_config()


# ============================================================================
# .env TEMPLATE
# ============================================================================
# Copy the following template to a .env file in the project root to override
# any configuration defaults:
#
# SERVER_HOST=0.0.0.0
# SERVER_PORT=5000
# DEBUG=False
# MODEL_PATH=models/saved_models
# DEFAULT_PIT_TIME_LOSS=22
# MAX_RACE_LAPS=78
# ============================================================================
