import asyncio
import requests
from beacon.beacon_scanner import FeasyBeaconScanner

MAC_BEACON = "DC:0D:30:1F:66:1C" 
NOMBRE_BEACON = "FSC-BP104D"
URL_API = "http://127.0.0.1:5000/api/beacon" 

async def vigilar_puerta():
    scanner = FeasyBeaconScanner(target_mac=MAC_BEACON, target_name=NOMBRE_BEACON, app_instance=None)
    print(f"[*] Escáner iniciado. Vigilando MAC: {MAC_BEACON}...")

    while True:
        data = await scanner.scan_beacon(duration=5)
        
        if data:
            distancia = data['reading']['distance_meters']
            print(f"[*] Paciente detectado a {distancia}m de la puerta.")
            
            estado = "ZONA_SEGURA" if distancia < 5.0 else "ALERTA_ALEJAMIENTO"
            
            payload = {
                "dispositivo": "beacon_puerta_principal",
                "distancia_metros": distancia,
                "estado": estado
            }
            
            try:
                requests.post(URL_API, json=payload)
            except Exception as e:
                print(f"[-] Error conectando con la API: {e}")
        else:
            print("[-] Paciente no detectado (Fuera del rango del Beacon).")
            
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(vigilar_puerta())