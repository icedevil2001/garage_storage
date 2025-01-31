from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from .extensions import db
from . import models
from .routes import main
import os
# from .config import Config
from pathlib import Path

# db = SQLAlchemy()
# migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garage_storage.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = Path('app') / 'static' / 'uploads'
    app.config['THUMBNAIL_FOLDER'] = Path('app') / 'static' / 'uploads' /'thumbnails'
    app.config['QR_FOLDER'] = Path('app') / 'static' /'qr_codes' 
    app.config['ASSETS_FOLDER'] = Path('app') / 'static' / 'assets'
    app.config["DROP_ALL_TABLES"] = False

    
    # Ensure upload directories exist
    app.config['UPLOAD_FOLDER'].mkdir( exist_ok=True)
    app.config['QR_FOLDER'].mkdir(exist_ok=True)
    app.config['THUMBNAIL_FOLDER'].mkdir( exist_ok=True)
    app.config['ASSETS_FOLDER'].mkdir( exist_ok=True)


    db.init_app(app)
    # migrate.init_app(app, db)
    
    with app.app_context():
        # Drop all tables and recreate them
        if app.config['DROP_ALL_TABLES']:
            db.drop_all()
        db.create_all()

    app.register_blueprint(main)

    return app

