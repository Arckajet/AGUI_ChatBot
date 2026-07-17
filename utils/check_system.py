import os
import sys
import json
import socket
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from pyngrok import ngrok, conf

load_dotenv()
# --- CONFIGURACIÓN ---
PORT = 8000
DATA_DIR = "data"
# Reemplaza esto con tu token real de Ngrok (búscalo en dashboard.ngrok.com)
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")

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


def start_ngrok(port):
    """Configura el token de Ngrok e inicia el túnel."""
    print("🌐 Configurando e iniciando Ngrok...")
    if NGROK_AUTHTOKEN == "TU_TOKEN_DE_NGROK_AQUÍ" or not NGROK_AUTHTOKEN:
        print("  ⚠️ Alerta: No has puesto tu token de Ngrok en la variable NGROK_AUTHTOKEN.")
        print("  La sesión podría expirar en un par de horas si no configuras el token.")
        return
        
    try:
        # Configurar el authtoken de manera persistente
        conf.get_default().auth_token = NGROK_AUTHTOKEN
        
        # Abrir el túnel HTTP en el puerto indicado
        public_url = ngrok.connect(port, "http")
        print("\n🚀 ¡TODO LISTO Y EN LÍNEA!")
        print(f"🔗 Tu URL pública de Ngrok es: {public_url}")
        print("💡 Copia esta URL en la configuración de tu webhook de Telegram, WhatsApp o Discord.\n")
    except Exception as e:
        print(f"  ❌ Error al iniciar Ngrok: {e}")


def main():
    print("=" * 50)
    print("🚀 INICIANDO CONTROL DE SALUD DEL SISTEMA (Elias Tool) 🚀")
    print("=" * 50)
    
    # 1. Comprobar carpetas
    check_directories()
    
    # 2. Comprobar JSONs
    if not check_json_files():
        print("\n💥 El sistema no puede arrancar debido a fallos en los archivos JSON.")
        sys.exit(1)
        
    # 3. Comprobar que el puerto 8000 no esté bloqueado
    if not is_port_free(PORT):
        print(f"\n💥 Libera el puerto {PORT} antes de volver a ejecutar el bot.")
        sys.exit(1)
        
    # 4. Si todo está perfecto, levantar Ngrok
    print("\n✅ Chequeo de salud del sistema exitoso.")
    start_ngrok(PORT)
    
    print("💬 Ahora puedes iniciar el servidor de tu chatbot en otra terminal.")
    print("=" * 50)

if __name__ == "__main__":
    main()