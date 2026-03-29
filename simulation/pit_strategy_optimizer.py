"""
Strategic Decision Layer for the F1 Race Strategy Engine.

This module acts as the single public interface between the Flask API layer
and the race simulation core. It validates race inputs, orchestrates the
simulation engine, and returns clean, structured strategy recommendations
ready for frontend consumption.
"""

import sys
import os
from typing import Dict, Any

# --- Cross-directory imports --- #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from backend.config import Config
from backend.logger import get_logger
from simulation.race_simulator import run_strategy_simulation

# --- Logger initialization --- #
logger = get_logger(__name__)


# ============================================================================
# SUPPORTED COMPOUND GUARD
# ============================================================================

VALID_COMPOUNDS: list = ["Soft", "Medium", "Hard", "Intermediate", "Wet"]


# ============================================================================
# MAIN STRATEGY OPTIMIZER FUNCTION
# ============================================================================

def optimize_strategy(
    track: str,
    lap_number: int,
    tyre_compound: str
) -> Dict[str, Any]:
    """
    Public interface for the F1 pit strategy optimizer.

    Validates race inputs, delegates to the race simulation engine,
    and returns a structured strategy recommendation dictionary.

    Args:
        track (str): Circuit name (e.g. 'Monaco', 'Silverstone').
        lap_number (int): Current race lap (reserved for live strategy
            extensions; currently influences logging only).
        tyre_compound (str): Starting tyre compound (e.g. 'Medium').

    Returns:
        Dict[str, Any]: Optimal strategy result with pit recommendations,
            projected time, tyre strategy, and simulation sweep data;
            or structured error response if optimization fails.
    """

    # --- Step 1: Request Logging --- #
    logger.info(
        f"🏎️  Strategy optimization requested — "
        f"Track: {track} | Lap: {lap_number} | Compound: {tyre_compound}"
    )

    # --- Step 2: Input Validation --- #

    # Circuit validation
    if track not in Config.SUPPORTED_CIRCUITS:
        logger.warning(
            f"⚠️  Unknown circuit '{track}' — not in supported circuit list. "
            f"Proceeding with simulation using default lap time baseline."
        )

    # Compound validation
    if tyre_compound not in VALID_COMPOUNDS:
        logger.warning(
            f"⚠️  Unrecognised tyre compound '{tyre_compound}' — "
            f"defaulting to 'Medium' for simulation."
        )
        tyre_compound = "Medium"

    # Lap number validation
    if lap_number < 1 or lap_number > Config.MAX_RACE_LAPS:
        logger.warning(
            f"⚠️  Lap number {lap_number} out of valid race range "
            f"(1–{Config.MAX_RACE_LAPS}). Value noted but simulation uses "
            f"full race window."
        )

    # --- Step 3: Simulation Execution --- #
    try:
        logger.debug(
            f"Invoking race simulation engine — "
            f"Track: {track} | Compound: {tyre_compound}"
        )

        result = run_strategy_simulation(track, tyre_compound)

        # --- Step 4: Success Response --- #
        logger.info(
            f"✅ Strategy computed — Track: {track} | "
            f"Best Pit Lap: {result['best_pit_lap']} | "
            f"Projected Race Time: {result['predicted_time']}s | "
            f"Strategy: {tyre_compound} → {result['tyre_strategy'][-1]}"
        )

        return {
            "track": track,
            "lap_number": lap_number,
            "tyre_compound": tyre_compound,
            "best_pit_lap": result["best_pit_lap"],
            "predicted_time": result["predicted_time"],
            "tyre_strategy": result["tyre_strategy"],
            "all_pit_results": result.get("all_pit_results", {}),
            "strategy_status": "optimal"
        }

    # --- Step 5: Error Handling --- #
    except Exception as e:
        error_message = str(e)
        logger.error(
            f"❌ Strategy engine failure — "
            f"Track: {track} | Compound: {tyre_compound} | "
            f"Error: {error_message}"
        )

        return {
            "track": track,
            "lap_number": lap_number,
            "tyre_compound": tyre_compound,
            "error": "Strategy engine failure",
            "detail": error_message,
            "strategy_status": "failed"
        }
