# =====================================================================
# SCRIPT DE PRUEBA LOCAL - AGUIBOT (CON INTERFAZ VISUAL DE MENÚS)
# SIMULADOR DE ENTRADAS DE USUARIO POR CONSOLA
# =====================================================================
'''
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import database
'''
from estados import MaquinaEstadosAGUI


def simular_chat():
    bot = MaquinaEstadosAGUI()
    USER_ID_PRUEBA = "+584121234567"
    
    print("🤖 INTEGRACIÓN AGUIBOT: CORE + DATABASE + INTERFAZ")
    print("Escribe 'salir' para terminar.\n")
    
    # Arrancamos mostrando la bienvenida real de Roberto
    print(bot.procesar_transicion(USER_ID_PRUEBA, "hola"))
    
    while True:
        usuario_input = input("👤 Tú: ")
        
        if usuario_input.lower() == 'salir':
            print("\nSimulación finalizada.")
            break
            
        # El bot procesa y nos da la interfaz real estructurada
        respuesta_visual = bot.procesar_transicion(USER_ID_PRUEBA, usuario_input)
        print(respuesta_visual)
        if "¡Gracias por usar AGUI Chatbot!" in respuesta_visual:
            print("\n[INFO]: Sesión cerrada por el usuario.")
            break
if __name__ == "__main__":
    simular_chat()