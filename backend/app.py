"""
F1 Race Strategy Engine - Flask Application Entry Point

This module serves as the main entry point for the F1 Intelligent Race Strategy
& Simulation Engine backend. It initializes the Flask application, configures CORS
for frontend communication, registers API blueprints, and manages the server lifecycle.

The application exposes RESTful endpoints for race strategy optimization, simulation,
and real-time telemetry analysis.
"""

import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from routes import api_blueprint


# ============================================================================
# Logger Configuration
# ============================================================================

def setup_logger():
    """Configure logging for the application."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create console handler with INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


# ============================================================================
# Flask Application Factory
# ============================================================================

def create_app():
    """
    Create and configure the Flask application instance.

    Returns:
        Flask: Configured Flask application instance
    """
    # Initialize Flask application
    app = Flask('F1 Strategy Engine')

    # Enable CORS globally for frontend communication
    CORS(app)

    # ========================================================================
    # Health Check Endpoint
    # ========================================================================

    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint to verify API availability.

        Returns:
            dict: JSON response with status information
            int: HTTP status code 200
        """
        return jsonify({
            "status": "running",
            "engine": "F1 Strategy Engine",
            "version": "1.0.0"
        }), 200

    # ========================================================================
    # Blueprint Registration
    # ========================================================================

    # Register API blueprint with /api prefix
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Setup logger
    logger = setup_logger()

    # Log startup banner
    logger.info("🏎️  F1 Strategy Engine — Backend Ignition. Running on port 5000.")

    # Create Flask application
    app = create_app()

    # Read debug flag from environment variable (defaults to False for production)
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'

    # Start server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode
    )
