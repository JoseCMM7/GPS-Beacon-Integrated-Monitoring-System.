import socket

# Escucha en todas las interfaces de tu red local
HOST = '0.0.0.0'  
PORT = 9000       

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"[*] Servidor encendido. Escuchando en el puerto {PORT}...")

    while True:
        conn, addr = s.accept()
        with conn:
            print(f"\n[+] ¡Conexión entrante desde la IP: {addr}!")
            data = conn.recv(1024) 
            if not data:
                break
            
            # Imprimimos los datos tal cual llegan (en bytes)
            # Esto es clave porque a veces los GPS mandan datos en Hexadecimal
            print(f"[*] Datos crudos recibidos: {data}")