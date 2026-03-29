"""
Core Race Physics Simulation Engine for the F1 Race Strategy Engine.

This module models lap-by-lap race progression incorporating tyre degradation,
fuel mass reduction, pit stop penalties, and compound switching to estimate
total race duration across multiple strategy scenarios. Provides realistic
race simulation physics for strategy optimization and analysis.
"""

import math
import random
from typing import Dict, List, Tuple, Optional
import sys
import os

# --- Cross-directory imports --- #
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.config import Config
from backend.logger import get_logger

# --- Logger initialization --- #
logger = get_logger(__name__)


# ============================================================================
# TRACK BASE LAP TIME PROFILES
# ============================================================================

TRACK_BASE_LAP_TIMES: Dict[str, float] = {
    "Monaco": 72.0,        # Tight street circuit, low speed, high precision
    "Silverstone": 88.0,   # High-speed British classic, long straights
    "Monza": 80.0,         # Temple of speed, low downforce, flat-out pace
    "Spa": 102.0,          # Long and varied, weather-sensitive, elevation
    "Suzuka": 95.0         # Technical figure-of-eight, demanding layout
}
# Note: These represent ideal dry-condition lap times for a midfield car
# before compound and fuel effects are applied.


# ============================================================================
# TYRE COMPOUND DEGRADATION RATES
# ============================================================================

TYRE_DEGRADATION_RATES: Dict[str, float] = {
    "Soft": 0.08,          # Fast but burns quickly under stress
    "Medium": 0.05,        # Balanced all-rounder, stable degradation
    "Hard": 0.03,          # Durable compound, slower initial warm-up
    "Intermediate": 0.06,  # Transitional wet compound, moderate wear
    "Wet": 0.07            # Full wet weather compound, high wear in drying
}
# Represents lap time increase (seconds) per lap on given compound.


# ============================================================================
# TYRE CLIFF MODEL
# ============================================================================

TYRE_CLIFF_LAP: Dict[str, int] = {
    "Soft": 18,            # Cliff after 18 laps — sudden grip loss
    "Medium": 28,          # Cliff after 28 laps — gradual degradation
    "Hard": 38,            # Cliff after 38 laps — late-race penalties
    "Intermediate": 22,    # Cliff after 22 laps — wet transition point
    "Wet": 20              # Cliff after 20 laps — drying track hazard
}
# Once tyre age exceeds cliff threshold, degradation rate increases 1.5x.


# ============================================================================
# FUEL BURN BONUS MODEL
# ============================================================================

def fuel_time_bonus(lap: int, total_laps: int) -> float:
    """
    Calculate the lap time improvement due to fuel burn reduction.

    Cars lose approximately 1.5 seconds per lap at the start compared
    to the end of the race as fuel load reduces. This models realistic
    weight-based performance improvement throughout the race.

    Args:
        lap: Current lap number (1-indexed).
        total_laps: Total number of laps in the race.

    Returns:
        Fuel time bonus in seconds (negative value = improvement).
    """
    # --- Calculate fuel weight factor --- #
    fuel_factor: float = 1.5 * (1 - lap / total_laps)

    # --- Log fuel bonus at debug level --- #
    logger.debug(
        f"Fuel bonus at lap {lap}/{total_laps}: {fuel_factor:.3f}s"
    )

    # --- Return negative value (improvement) --- #
    return -fuel_factor


# ============================================================================
# SINGLE LAP TIME SIMULATION
# ============================================================================

def simulate_lap_time(
    track: str,
    compound: str,
    tyre_age: int,
    lap: int,
    total_laps: int
) -> float:
    """
    Simulate a single lap time using multiple physics factors.

    Combines track baseline, tyre degradation with cliff effect,
    fuel burn reduction, and random variation to produce realistic
    per-lap times. Enforces physical floor (97% of base lap time).

    Args:
        track: Circuit name (e.g., "Monaco", "Silverstone").
        compound: Tyre compound in use ("Soft", "Medium", "Hard", etc.).
        tyre_age: Number of laps completed on current tyres.
        lap: Current lap number (1-indexed).
        total_laps: Total laps in the race.

    Returns:
        Simulated lap time in seconds.
    """
    # --- Base lap time for track --- #
    base: float = TRACK_BASE_LAP_TIMES.get(track, 90.0)
    if track not in TRACK_BASE_LAP_TIMES:
        logger.warning(
            f"⚠️  Unknown track '{track}' — using default base lap time "
            f"of 90.0s"
        )

    # --- Tyre degradation with cliff effect --- #
    deg_rate: float = TYRE_DEGRADATION_RATES.get(compound, 0.05)
    cliff: int = TYRE_CLIFF_LAP.get(compound, 25)

    if tyre_age > cliff:
        degradation: float = tyre_age * deg_rate * 1.5  # Cliff penalty
    else:
        degradation: float = tyre_age * deg_rate

    # --- Fuel burn bonus --- #
    fuel_bonus: float = fuel_time_bonus(lap, total_laps)

    # --- Random variation (track surface, aero turbulence) --- #
    variation: float = random.uniform(-0.2, 0.2)

    # --- Calculate final lap time with physical floor --- #
    lap_time: float = base + degradation + fuel_bonus + variation
    lap_time = max(lap_time, base * 0.97)  # Never below 97% of base

    # --- Log detailed lap simulation --- #
    logger.debug(
        f"Lap {lap} | {compound} age {tyre_age} | "
        f"Degradation: +{degradation:.2f}s | Fuel: {fuel_bonus:.2f}s | "
        f"Lap Time: {lap_time:.3f}s"
    )

    return lap_time


# ============================================================================
# FULL RACE SIMULATION
# ============================================================================

def simulate_race(
    track: str,
    pit_lap: int,
    compound: str
) -> float:
    """
    Simulate a full race distance for a single pit strategy (one stop).

    Accumulates lap times pre-pit and post-pit, applies pit stop penalty,
    models tyre reset and compound change, and returns total race time.
    Represents a single-stop pit strategy throughout the race.

    Args:
        track: Circuit name.
        pit_lap: Lap number at which to execute pit stop (10-40).
        compound: Starting tyre compound.

    Returns:
        Total simulated race time in seconds.
    """
    # --- Initialize race state --- #
    total_laps: int = Config.MAX_RACE_LAPS
    total_time: float = 0.0
    tyre_age: int = 0
    pitted: bool = False
    current_compound: str = compound

    # --- Simulate each lap --- #
    for lap in range(1, total_laps + 1):

        # --- Check for pit stop execution --- #
        if not pitted and lap == pit_lap:
            total_time += Config.DEFAULT_PIT_TIME_LOSS
            tyre_age = 0
            current_compound = "Hard"
            pitted = True

            logger.info(
                f"🔧 Pit stop executed at lap {pit_lap} — "
                f"switching to Hard tyres (+{Config.DEFAULT_PIT_TIME_LOSS}s)"
            )

        # --- Simulate lap time --- #
        lap_time: float = simulate_lap_time(
            track, current_compound, tyre_age, lap, total_laps
        )
        total_time += lap_time
        tyre_age += 1

    # --- Log race completion --- #
    logger.debug(
        f"Race simulation complete — Track: {track} | "
        f"Pit Lap: {pit_lap} | Compound: {compound} | "
        f"Total Time: {total_time:.2f}s"
    )

    return total_time


# ============================================================================
# STRATEGY COMPARISON ENGINE
# ============================================================================

def run_strategy_simulation(
    track: str,
    compound: str
) -> Dict[str, object]:
    """
    Iterate through pit stop windows and find optimal strategy.

    Tests all candidate pit stop laps (10-40), simulates full race
    for each, and returns the pit lap producing the fastest race time.
    Provides complete breakdown for charting and analysis.

    Args:
        track: Circuit name.
        compound: Starting tyre compound.

    Returns:
        Dictionary containing:
            - best_pit_lap: Optimal lap for pit stop.
            - predicted_time: Total race time for best strategy.
            - tyre_strategy: List [starting_compound, "Hard"].
            - all_pit_results: Dict mapping pit_lap -> race_time.
    """
    # --- Initialize strategy search state --- #
    best_pit_lap: Optional[int] = None
    best_time: float = float("inf")
    all_results: Dict[int, float] = {}

    # --- Test all pit stop windows --- #
    for pit_lap in range(10, 41):
        race_time: float = simulate_race(track, pit_lap, compound)
        all_results[pit_lap] = race_time

        if race_time < best_time:
            best_time = race_time
            best_pit_lap = pit_lap

    # --- Log strategy conclusion --- #
    logger.info(
        f"✅ Optimal strategy found — Track: {track} | "
        f"Best Pit Lap: {best_pit_lap} | "
        f"Projected Time: {best_time:.2f}s | "
        f"Starting Compound: {compound} → Hard"
    )

    # --- Return strategy results --- #
    return {
        "best_pit_lap": best_pit_lap,
        "predicted_time": round(best_time, 2),
        "tyre_strategy": [compound, "Hard"],
        "all_pit_results": all_results
    }
