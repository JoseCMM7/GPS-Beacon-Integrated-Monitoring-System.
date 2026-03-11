import asyncio
import math
import struct
from datetime import datetime
from bleak import BleakScanner

class FeasyBeaconScanner:
    def __init__(self, target_mac, target_name, app_instance=None):
        self.target_mac = target_mac
        self.target_name = target_name
        self.app = app_instance
        self.default_tx_power = self.get_current_tx_power()
        self.ultimas_distancias = []
    
    def get_current_tx_power(self):
        """Obtiene el último TX Power configurado en la BD"""
        try:
            if self.app:
                with self.app.app_context():
                    from beacon.models import BeaconConfiguration
                    from sqlalchemy import select
                    from app import db
                    
                    stmt = select(BeaconConfiguration).where(
                        BeaconConfiguration.mac_address == self.target_mac,
                        BeaconConfiguration.valid_to == None
                    )
                    
                    result = db.session.execute(stmt)
                    current_config = result.scalar_one_or_none()
                    
                    if current_config:
                        print(f"📊 Usando TX Power configurado: {current_config.tx_power} dBm")
                        return current_config.tx_power
        except Exception as e:
            print(f"⚠️ Error leyendo configuración: {e}")
        
        print("📊 Usando TX Power por defecto: -59 dBm")
        return -59
    
    def normalize_mac(self, mac):
        """Normaliza MAC address para comparación"""
        if mac is None:
            return ""
        return mac.upper().replace(":", "").replace("-", "")
    
    def parse_ibeacon_data(self, manufacturer_data):
        """Parsea datos en formato iBeacon"""
        if 0x004C not in manufacturer_data:
            return None
        
        data = manufacturer_data[0x004C]
        
        if len(data) < 23 or data[0] != 0x02 or data[1] != 0x15:
            return None
        
        uuid = data[2:18].hex()
        uuid_formatted = f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"
        
        major = struct.unpack('>H', data[18:20])[0]
        minor = struct.unpack('>H', data[20:22])[0]
        tx_power = struct.unpack('b', data[22:23])[0]
        
        return {
            'uuid': uuid_formatted,
            'major': major,
            'minor': minor,
            'tx_power': tx_power
        }
    
    def calculate_distance(self, rssi, tx_power):
        """Calcula distancia usando fórmula de path loss"""
        if rssi == 0 or tx_power == 0:
            return -1.0
        
        try:
            ratio = rssi * 1.0 / tx_power
            if ratio < 1.0:
                distance = math.pow(ratio, 10)
            else:
                distance = (0.89976) * math.pow(ratio, 7.7095) + 0.111
            
            return round(min(distance, 100.0), 2)
        except:
            return -1.0
    
    def calculate_smoothed_distance(self, nueva_distancia):
        """Promedio móvil de las últimas 5 lecturas"""
        if nueva_distancia > 0:
            self.ultimas_distancias.append(nueva_distancia)
            if len(self.ultimas_distancias) > 5:
                self.ultimas_distancias.pop(0)
            
            if len(self.ultimas_distancias) > 0:
                return sum(self.ultimas_distancias) / len(self.ultimas_distancias)
        return nueva_distancia
    
    def get_distance_color(self, distance):
        """Determina el color según la distancia"""
        if distance < 0:
            return 'gray'
        elif distance < 2:
            return 'green'
        elif distance < 5:
            return 'yellow'
        else:
            return 'red'
    
    async def scan_beacon(self, duration=5):
        """Escanea el beacon y retorna datos"""
        self.default_tx_power = self.get_current_tx_power()
        
        print(f"🔍 Buscando beacon {self.target_name} (TX Power: {self.default_tx_power} dBm)...")
        
        try:
            devices = await BleakScanner.discover(timeout=duration, return_adv=True)
        except Exception as e:
            print(f"❌ Error en escaneo Bluetooth: {e}")
            return None
        
        target_normalized = self.normalize_mac(self.target_mac)
        
        for address, (device, adv_data) in devices.items():
            current_normalized = self.normalize_mac(address)
            device_name = device.name if device.name else ""
            
            if (current_normalized == target_normalized or 
                (device_name and device_name == self.target_name)):
                
                ibeacon_data = self.parse_ibeacon_data(adv_data.manufacturer_data)
                
                tx_power = self.default_tx_power
                uuid = None
                major = None
                minor = None
                
                if ibeacon_data:
                    uuid = ibeacon_data['uuid']
                    major = ibeacon_data['major']
                    minor = ibeacon_data['minor']
                    print(f"📱 Beacon detectado - TX Power del dispositivo: {ibeacon_data['tx_power']} dBm (usando config: {tx_power} dBm)")
                
                distance = self.calculate_distance(adv_data.rssi, tx_power)
                smoothed_distance = self.calculate_smoothed_distance(distance)
                color = self.get_distance_color(smoothed_distance)
                
                print(f"📊 RSSI: {adv_data.rssi} dBm → Distancia: {smoothed_distance:.2f}m")
                
                service_uuids_str = ''
                if adv_data.service_uuids:
                    service_uuids_str = ','.join([str(u) for u in adv_data.service_uuids])
                
                beacon_data = {
                    'mac_address': address,
                    'device_name': device_name or self.target_name,
                    'model': 'FSC-BP104D',
                    'uuid': uuid,
                    'major': major,
                    'minor': minor
                }
                
                config_data = {
                    'mac_address': address,
                    'tx_power': tx_power,
                    'valid_from': datetime.now(),
                    'valid_to': None
                }
                
                # DATOS DE LECTURA - SIN raw_packet_data
                reading_data = {
                    'mac_address': address,
                    'rssi': adv_data.rssi,
                    'distance_meters': smoothed_distance,
                    'tx_power': tx_power,
                    'manufacturer_data_hex': adv_data.manufacturer_data[0x004C].hex() if 0x004C in adv_data.manufacturer_data else '',
                    'service_uuids': service_uuids_str,
                    'timestamp': datetime.now()
                }
                
                complete_data = {
                    'beacon': beacon_data,
                    'configuration': config_data,
                    'reading': reading_data,
                    'color': color
                }
                
                return complete_data
        
        print(f"❌ Beacon no encontrado")
        return None