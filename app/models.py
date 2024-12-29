from datetime import datetime
from .extensions import db

class Box(db.Model):
    id = db.Column(db.String(8), primary_key=True)  # Unique ID for each box
    name = db.Column(db.String(100), nullable=False)  # Box name
    description = db.Column(db.Text)  # Box description
    location = db.Column(db.String(100))  # Add this line
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp for when the box was created
    qr_code_id = db.Column(db.String(8), unique=True, nullable=False)  # QR code ID in format AA123456
    qr_code = db.Column(db.String(200), nullable=True)  # Path to QR code image can be null initially
    items = db.relationship('Item', backref='box', lazy=True)  # One-to-many relationship with Item

    def __repr__(self):
        return f"<Box {self.name}>"

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each item
    name = db.Column(db.String(100), nullable=False)  # Item name
    description = db.Column(db.Text)  # Item description
    image_path = db.Column(db.String(200), nullable=True)  # Path to item image
    box_id = db.Column(db.String(8), db.ForeignKey('box.id'), nullable=False)  # Foreign key to Box
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp for when the item was created

    def __repr__(self):
        return f"<Item {self.name} in Box {self.box_id}>"
