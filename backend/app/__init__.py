"""
Flask application factory.
Initializes the application with all configurations and extensions.
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import config
from app.utils.database import db
from app.routes import register_routes
from app.models import User, Camera, Alert, Activity, AllowedPerson


def create_app(config_name='default'):
    """
    Create and configure Flask application.
    
    Args:
        config_name: Configuration name (development/production/testing)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    # CORS configuration - allow credentials and all methods
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    JWTManager(app)
    
    # Register routes
    register_routes(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'message': 'Smart CCTV API is running'
        }, 200
    
    return app

