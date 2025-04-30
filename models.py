from datetime import datetime
from database import db

class ScanHistory(db.Model):
    __tablename__ = 'scan_history'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    active_count = db.Column(db.Integer, default=0)
    inactive_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)
    
    # One-to-many relationship with ScanResult
    results = db.relationship('ScanResult', backref='scan', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ScanHistory {self.domain} ({self.timestamp})>"


class ScanResult(db.Model):
    __tablename__ = 'scan_results'
    
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scan_history.id'), nullable=False)
    subdomain = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    response_info = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScanResult {self.subdomain} {'active' if self.is_active else 'inactive'}>"