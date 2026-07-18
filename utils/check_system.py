# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os
import sys
import json
import socket
import subprocess

load_dotenv()
# --- CONFIGURACIÓN ---
PORT = 8000
DATA_DIR = "data"

# Lista de archivos JSON esenciales que deberían existir en data/
# Si no existen, el script los creará vacíos ({}) para que no falle el bot.
ESSENTIAL_JSONS = ["config.json", "users.json"] 


def check_directories():
    """Verifica que la carpeta data/ exista. Si no, la crea."""
    print("📁 Verificando directorios...")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"  └─ Creando carpeta faltante: '{DATA_DIR}/'")
    else:
        print(f"  └─ Carpeta '{DATA_DIR}/' detectada correctamente.")


def check_json_files():
    """Verifica que los archivos JSON en data/ existan y tengan un formato válido."""
    print("🔍 Verificando archivos JSON...")
    
    for filename in ESSENTIAL_JSONS:
        filepath = os.path.join(DATA_DIR, filename)
        
        # Si el archivo no existe, lo creamos con una estructura JSON básica vacía
        if not os.path.exists(filepath):
            print(f"  ⚠️ '{filename}' no existía. Creando archivo vacío...")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4)
            continue
            
        # Si existe, verificamos que no esté corrupto
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"  └─ {filename}: Estructura válida ✓")
        except json.JSONDecodeError as e:
            print(f"  ❌ ERROR: El archivo '{filename}' tiene un formato JSON inválido!")
            print(f"     Detalle del error: {e}")
            return False
    return True


def is_port_free(port):
    """Verifica si el puerto especificado está libre."""
    print(f"🔌 Verificando puerto {port}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Si connect_ex devuelve 0, significa que el puerto está ocupado
        result = s.connect_ex(('127.0.0.1', port))
        if result == 0:
            print(f"  ❌ ERROR: El puerto {port} ya está en uso por otra aplicación.")
            return False
        else:
            print(f"  └─ Puerto {port} disponible ✓")
            return True


def start_localtunnel(port):
    """Inicia el túnel de LocalTunnel en segundo plano."""
    print("🌐 Iniciando LocalTunnel...")
    try:
        # Ejecutamos localtunnel (lt) en segundo plano sin bloquear el hilo principal.
        # En Windows, lt se instala como un script de node (a menudo requiere shell=True).
        process = subprocess.Popen(
            ["lt", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        # Esperamos un momento para leer la URL generada en stdout
        import time
        time.sleep(3)
        
        # Intentamos obtener la primera línea de salida que suele contener la URL
        # Ojo: Popen.poll() comprueba si el proceso sigue vivo
        if process.poll() is None:
            # En lugar de un hilo eterno, leemos una vez de forma controlada
            # para capturar la URL sin dejar un hilo "huérfano" al cerrar
            def read_once():
                try:
                    for line in iter(process.stdout.readline, ''):
                        if "your url is:" in line:
                            print(f"\n🚀 ¡TUNEL EN LÍNEA!")
                            print(f"🔗 {line.strip()}")
                            break
                except:
                    pass
            
            import threading
            t = threading.Thread(target=read_once, daemon=True)
            t.start()
            t.join(timeout=2) # Espera máximo 2 segundos para imprimir la URL y sigue
        else:
            stdout, stderr = process.communicate()
            print(f" ❌ Error al iniciar LocalTunnel: {stderr or stdout}")
            
    except Exception as e:
        print(f" ❌ Error al ejecutar LocalTunnel: {e}")


def main() -> bool:
    """Run all health checks. Returns True if the system is healthy, False otherwise."""
    print("=" * 50)
    print("🚀 INICIANDO CONTROL DE SALUD DEL SISTEMA (Elias Tool) 🚀")
    print("=" * 50)

    # 1. Comprobar carpetas
    check_directories()

    # 2. Comprobar JSONs
    if not check_json_files():
        print("\n💥 El sistema no puede arrancar debido a fallos en los archivos JSON.")
        return False

    # 3. Comprobar que el puerto 8000 no esté bloqueado
    if not is_port_free(PORT):
        print(f"\n💥 Libera el puerto {PORT} antes de volver a ejecutar el bot.")
        return False

    # 4. Si todo está perfecto, levantar LocalTunnel
    print("\n✅ Chequeo de salud del sistema exitoso.")
    start_localtunnel(PORT)

    print("💬 Ahora puedes iniciar el servidor de tu chatbot en otra terminal.")
    print("=" * 50)
    return True

if __name__ == "__main__":
    if not main():
        sys.exit(1)