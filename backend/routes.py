"""
API Routes Layer for the F1 Race Strategy Engine.

This module serves as the HTTP request handler layer for the F1 Intelligent Race Strategy
& Simulation Engine, accepting incoming REST API calls and delegating computational logic
to the simulation layer. All endpoints are registered under the /api blueprint prefix.
"""

import os
import sys
import logging
from flask import Blueprint, request, jsonify

# --- Cross-directory imports --- #
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from simulation.pit_strategy_optimizer import optimize_strategy  # noqa: E402

# --- Logger initialization --- #
logger = logging.getLogger(__name__)

# --- Blueprint setup --- #
api_routes = Blueprint('api_routes', __name__, url_prefix='/api')


# ============================================================================
# ENDPOINT 1: Track Information
# ============================================================================

@api_routes.route('/tracks', methods=['GET'])
def get_tracks():
    """
    Retrieve the list of circuits supported by the F1 Race Strategy Engine.

    Returns:
        JSON response containing available tracks and total count.
        Status Code: 200 (OK)
    """
    logger.info("Track list requested.")

    # --- Response --- #
    response = {
        "tracks": ["Monaco", "Silverstone", "Monza", "Spa", "Suzuka"],
        "total": 5
    }

    return jsonify(response), 200


# ============================================================================
# ENDPOINT 2: Engine Metadata
# ============================================================================

@api_routes.route('/engine_info', methods=['GET'])
def get_engine_info():
    """
    Retrieve metadata and status information about the running strategy engine instance.

    Returns:
        JSON response containing engine name, version, status, and available models.
        Status Code: 200 (OK)
    """
    logger.info("Engine info requested.")

    # --- Response --- #
    response = {
        "engine": "F1 Race Strategy Engine",
        "version": "1.0.0",
        "status": "active",
        "models": ["lap_time", "tyre_degradation", "safety_car"]
    }

    return jsonify(response), 200


# ============================================================================
# ENDPOINT 3: Strategy Prediction
# ============================================================================

@api_routes.route('/predict_strategy', methods=['POST'])
def predict_strategy():
    """
    Compute an optimal pit stop strategy based on race conditions.

    Accepts a JSON payload containing track information, lap number, and tyre compound.
    Validates input, delegates to the simulation engine, and returns strategy results.

    Expected Request Body:
        {
            "track": str,
            "lap_number": int,
            "tyre_compound": str
        }

    Returns:
        Success (200): Strategy computation result with pit stop recommendation
        Bad Request (400): Missing required fields
        Unprocessable Entity (422): Invalid tyre compound
        Server Error (500): Strategy engine failure
    """
    # --- Validation --- #
    data = request.get_json()

    if not data:
        logger.warning("Strategy request received with no JSON body.")
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # Check for required fields
    required_fields = ["track", "lap_number", "tyre_compound"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        logger.warning(
            f"Strategy request missing required fields: {', '.join(missing_fields)}"
        )
        return jsonify({
            "error": f"Missing required fields: {', '.join(required_fields)}"
        }), 400

    track = data.get("track")
    lap_number = data.get("lap_number")
    tyre_compound = data.get("tyre_compound")

    # Validate tyre compound
    valid_compounds = ["Soft", "Medium", "Hard", "Intermediate", "Wet"]
    if tyre_compound not in valid_compounds:
        logger.warning(
            f"Strategy request received with invalid tyre compound: {tyre_compound}"
        )
        return jsonify({
            "error": (
                f"Invalid tyre compound. Must be one of: "
                f"{', '.join(valid_compounds)}"
            )
        }), 422

    # Log incoming request
    logger.info(
        f"Strategy request received — Track: {track} | Lap: {lap_number} | "
        f"Compound: {tyre_compound}"
    )

    # --- Processing --- #
    try:
        strategy_result = optimize_strategy(track, lap_number, tyre_compound)

        logger.info(f"Strategy computed successfully for {track}.")

        # --- Response --- #
        return jsonify(strategy_result), 200

    except Exception as e:
        error_message = str(e)
        logger.error(f"Strategy engine error for {track}: {error_message}")

        return jsonify({
            "error": "Strategy simulation failed.",
            "detail": error_message
        }), 500

        # ---------------------------------------------------
# GET /strategy_graph
# ---------------------------------------------------

@api_routes.route("/strategy_graph", methods=["GET"])
def strategy_graph():
    """
    Returns pit strategy curve data for visualization.
    """

    try:

        track = request.args.get("track", "Monaco")
        compound = request.args.get("compound", "Medium")

        logger.info(
            f"Strategy graph requested — Track: {track} | Compound: {compound}"
        )

        result = optimize_strategy(track, 1, compound)

        pit_results = result.get("all_pit_results", {})

        pit_laps = list(pit_results.keys())
        race_times = list(pit_results.values())

        return jsonify({
            "track": track,
            "compound": compound,
            "pit_laps": pit_laps,
            "race_times": race_times
        })

    except Exception as e:

        logger.error(f"Strategy graph generation failed: {str(e)}")

        return jsonify({
            "error": "Strategy graph generation failed",
            "detail": str(e)
        }), 500
