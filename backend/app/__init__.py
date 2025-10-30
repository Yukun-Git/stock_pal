"""Flask application factory."""

from flask import Flask
from flask_cors import CORS
from flask_restful import Api

from app.config import config


def create_app(config_name='development'):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Create API instance
    api = Api(app)

    # Register blueprints
    from app.api.v1 import register_routes
    register_routes(api)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'version': app.config['API_VERSION']}, 200

    return app
