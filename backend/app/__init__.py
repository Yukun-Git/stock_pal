"""Flask application factory."""

from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager

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

    # Initialize JWT
    jwt = JWTManager(app)

    # Create API instance
    api = Api(app)

    # Register REST API routes
    from app.api.v1 import register_routes
    register_routes(api)

    # Register auth blueprint
    from app.api.v1.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'version': app.config['API_VERSION']}, 200

    return app
