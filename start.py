# start.py
import subprocess
import time

def iniciar_proyecto():
    # 1. Ejecutar el chequeo de Elias
    print("Iniciando chequeo de salud...")
    resultado = subprocess.run(["python", "utils/check_system.py"])
    
    if resultado.returncode == 0:
        # 2. Si el chequeo es exitoso, lanzar el bot (FastAPI)
        print("Salud confirmada. Iniciando FastAPI...")
        subprocess.run(["uvicorn", "main:app", "--reload"])
    else:
        print("Error en el chequeo de salud. Abortando...")

if __name__ == "__main__":
    iniciar_proyecto()