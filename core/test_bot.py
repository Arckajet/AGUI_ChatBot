# =====================================================================
# SCRIPT DE PRUEBA LOCAL - AGUIBOT (CON INTERFAZ VISUAL DE MENÚS)
# SIMULADOR DE ENTRADAS DE USUARIO POR CONSOLA
# =====================================================================
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import database
from estados import MaquinaEstadosAGUI
print("🔍 --- DIAGNÓSTICO DE RUTAS ---")
print("📍 Tu CMD está parado en:", os.getcwd())
ruta_pasteleria = os.path.abspath("../data/pasteleria.json")
print("📂 Buscando el JSON en:", ruta_pasteleria)
print("❓ ¿El archivo existe físicamente?:", os.path.exists(ruta_pasteleria))

if os.path.exists(ruta_pasteleria):
    print("📄 Contenido real del JSON de Elias:")
    print(database.leer_inventario(ruta_pasteleria))
print("🔍 -----------------------------\n")

def mostrar_menu_visual(estado, db_actual):
    """Pinta en la consola las opciones disponibles según el estado actual (UX/UI Core)"""
    print("-" * 50)
    
    if estado == "MENU_PRINCIPAL":
        print("🏪 ** MENÚ PRINCIPAL DE AGUIBOT **")
        print("Selecciona una opción digitando el número:")
        print(" [1] 🍰 Ir a la Tienda de Pastelería")
        print(" [2] 🎮 Ir a la Tienda de Videojuegos")
        print(" [3] 🛒 Ver mi Carrito de Compras")
        print(" [4] 🛠️ Contactar a Soporte Técnico / Crear Ticket")
        print(" [salir] Para salir del simulador")
        
    elif estado == "VISTA_CATALOGO":
        tienda = "PASTELERÍA" if "pasteleria" in db_actual else "VIDEOJUEGOS"
        print(f"📦 ** CATÁLOGO DE {tienda} **")
        print("Ingresa el ID del producto que deseas agregar al carrito.")
        print(" *(Nota: En pasteleria.json existen los IDs '1' y '2')*")
        print(" [0] ↩️ Volver al Menú Principal")
        
    elif estado == "VISTA_CARRITO":
        print("🛒 ** TU CARRITO DE COMPRAS **")
        print(" [1] 💳 Proceder al Pago Seguro")
        print(" [2] 🗑️ Vaciar todo el Carrito")
        print(" [0] ↩️ Volver al Menú Principal")
        
    elif estado == "MENU_SOPORTE":
        print("🛠️ ** CENTRO DE SOPORTE TÉCNICO **")
        print(" [1] 📝 Generar un Ticket de Falla")
        print(" [0] ↩️ Volver al Menú Principal")
        
    print("-" * 50)

def simular_chat():
    bot = MaquinaEstadosAGUI()
    USER_ID_PRUEBA = "+584121234567"
    
    print("=" * 60)
    print("🤖 SIMULADOR INTEGRADO DE AGUIBOT (CON MENÚS DE INTERFAZ)")
    print(f"📱 Conectado con el usuario simulado: {USER_ID_PRUEBA}")
    print("Escribe 'salir' en cualquier momento para terminar la simulación.")
    print("=" * 60)
    
    while True:
        # 1. Recuperamos la sesión actual
        sesion_actual = bot.obtener_o_crear_sesion(USER_ID_PRUEBA)
        estado_previo = sesion_actual["estado"]
        db_actual = sesion_actual["tienda_actual"]
        
        # 2. PINTAMOS EL MENÚ DINÁMICO (Aporte UX/UI de Ángel)
        mostrar_menu_visual(estado_previo, db_actual)
        
        # 3. Capturamos la entrada del teclado
        usuario_input = input("👤 Tú: ")
        
        if usuario_input.lower() == 'salir':
            print("\nSimulación finalizada.")
            break
            
        # 4. Procesamos la entrada en la máquina de estados
        resultado_accion = bot.procesar_transicion(USER_ID_PRUEBA, usuario_input)
        
        # 5. Mostramos el resultado del procesamiento lógico
        print(f"\n⚙️ [LOG]: Estado cambió a -> **{resultado_accion}**")

if __name__ == "__main__":
    simular_chat()