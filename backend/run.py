"""Application entry point."""

import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create Flask app
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Get port from environment variable or use 4001 as default
    port = int(os.environ.get('PORT', 4001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
