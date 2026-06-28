import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in {"1", "true", "yes"}

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "student_mental_health_dss")
    DB_PORT = int(os.getenv("DB_PORT", 3306))


def create_app() -> Flask:
    # Use the current working directory as the base
    # This should be the project root when running python app.py
    base_dir = os.getcwd()
    
    template_folder = os.path.join(base_dir, 'templates')
    static_folder = os.path.join(base_dir, 'static')
    static_url_path = '/static'
    
    # Create Flask app with explicit root_path, template and static folder paths
    # The root_path is critical - it's used for resolving resources
    app = Flask(
        __name__,
        root_path=base_dir,  # Explicitly set root_path to project root
        template_folder=template_folder,
        static_folder=static_folder,
        static_url_path=static_url_path
    )
    
    app.config.from_object(Config)

    from routes import register_routes

    register_routes(app)

    return app
