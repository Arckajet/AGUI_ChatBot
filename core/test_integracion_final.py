import sys
import os
# Aseguramos rutas para importar desde core y utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from estados import MaquinaEstadosAGUI
from utils.ux_helper import UXHelper

def prueba_integracion():
    print("--- INICIANDO PRUEBA DE INTEGRACIÓN ---")
    bot = MaquinaEstadosAGUI()
    
    # 1. Prueba de Manual (Roberto)
    print("\n[TEST 1] Verificando manual de usuario...")
    respuesta = UXHelper.get_user_manual()
    if "GUÍA DE USO RÁPIDO" in respuesta and "COMANDOS PRINCIPALES" in respuesta:
        print("✅ PASS: Manual formateado correctamente.")
    else:
        print("❌ FAIL: El manual no tiene el formato esperado.")

    # 2. Prueba de flujo real (Tu core + UI de Roberto)
    print("\n[TEST 2] Verificando respuesta del bot con formato UI...")
    user_id = "+58412000000"
    
    # Simulación de respuesta del bot
    res = bot.procesar_transicion(user_id, "1")
    
    # Aplicamos formato si no lo tiene ya integrado en el estado
    respuesta_final = UXHelper.format_success(res)
    
    if "✅ ¡Hecho!" in respuesta_final:
        print("✅ PASS: Integración de UI en respuesta exitosa.")
        print(f"Respuesta final visual:\n{respuesta_final}")
    else:
        print("❌ FAIL: No se pudo aplicar el formato de éxito.")

    print("\n--- PRUEBA FINALIZADA ---")

if __name__ == "__main__":
    prueba_integracion()