from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Beacon(db.Model):
    __tablename__ = 'beacon'
    
    mac_address = db.Column(db.String(17), primary_key=True)
    device_name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    uuid = db.Column(db.String(36))
    major = db.Column(db.Integer)
    minor = db.Column(db.Integer)
    
    configurations = db.relationship('BeaconConfiguration', backref='beacon', lazy=True, cascade='all, delete-orphan')
    readings = db.relationship('BeaconReading', backref='beacon', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'mac_address': self.mac_address,
            'device_name': self.device_name,
            'model': self.model,
            'uuid': self.uuid,
            'major': self.major,
            'minor': self.minor
        }

class BeaconConfiguration(db.Model):
    __tablename__ = 'beacon_configurations'
    
    id_conf = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mac_address = db.Column(db.String(17), db.ForeignKey('beacon.mac_address', ondelete='CASCADE'), nullable=False)
    tx_power = db.Column(db.Integer, nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.now)
    valid_to = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id_conf,
            'mac_address': self.mac_address,
            'tx_power': self.tx_power,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None
        }

class BeaconReading(db.Model):
    __tablename__ = 'beacon_readings'
    
    id_reading = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    mac_address = db.Column(db.String(17), db.ForeignKey('beacon.mac_address', ondelete='CASCADE'), nullable=False)
    rssi = db.Column(db.Integer, nullable=False)
    distance_meters = db.Column(db.Float)
    tx_power = db.Column(db.Integer)
    manufacturer_data_hex = db.Column(db.Text)
    service_uuids = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    # 👆 raw_packet_data ELIMINADO
    
    def to_dict(self):
        return {
            'id': self.id_reading,
            'mac_address': self.mac_address,
            'rssi': self.rssi,
            'distance': round(self.distance_meters, 2) if self.distance_meters else None,
            'tx_power': self.tx_power,
            'manufacturer_data': self.manufacturer_data_hex,
            'service_uuids': self.service_uuids,
            'timestamp': self.timestamp.isoformat()
            # 👆 raw_packet ELIMINADO
        }