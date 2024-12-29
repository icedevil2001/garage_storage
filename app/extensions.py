from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def init_app(app):
    """Initialize all extensions with the Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Set login view for @login_required decorator
    login_manager.login_view = 'auth.login'