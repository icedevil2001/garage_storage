from flask import Flask
from .extensions import db
from . import models
from .routes import main
import os
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garage_storage.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
    app.config['QR_FOLDER'] = os.path.join('app', 'static', 'qr_codes')

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

    db.init_app(app)
    
    with app.app_context():
        # Drop all tables and recreate them
        if Config.DROP_ALL_TABLES:
            db.drop_all()
        db.create_all()

    app.register_blueprint(main)

    return app

