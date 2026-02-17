"""
Application entry point.
Run the Flask development server.
"""
import os
from app import create_app

# Get configuration from environment or default to development
config_name = os.getenv('FLASK_ENV', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5001)),
        debug=(config_name == 'development')
    )

