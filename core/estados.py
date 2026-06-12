import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data import database  # <-- INTEGRACIÓN: Importamos el módulo real de Elias

class MaquinaEstadosAGUI:
    def __init__(self):
        # Memoria caché en servidor para persistencia de sesiones de usuarios
        # Ahora guardamos un diccionario interno por usuario: {"id_usuario": {"estado": "...", "tienda_actual": "..."}}
        self.sesiones = {}
        
        # Definición de los Estados Finitos de la CUI
        self.ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"
        self.ESTADO_CATALOGO = "VISTA_CATALOGO"
        self.ESTADO_CARRITO = "VISTA_CARRITO"
        self.ESTADO_SOPORTE = "MENU_SOPORTE"
        
        # Rutas de base de datos asignadas por el negocio (Elias)
        # Asegúrate de tener estos archivos .json creados en tu carpeta para las pruebas
        self.DB_PASTELERIA = "../data/inventario_pasteleria.json"
        self.DB_VIDEOJUEGOS = "../data/inventario_videojuegos.json"

    def obtener_o_crear_sesion(self, user_id: str) -> dict:
        """Módulo 0: Handshake - Recupera o inicializa la estructura de sesión del cliente"""
        if user_id not in self.sesiones:
            self.sesiones[user_id] = {
                "estado": self.ESTADO_MENU_PRINCIPAL,
                "tienda_actual": self.DB_PASTELERIA # Por defecto inicia en pastelería, cambiará según su selección
            }
        return self.sesiones[user_id]

    def procesar_transicion(self, user_id: str, user_input: str) -> str:
        """Cerebro del Bot: Evalúa la entrada y altera el estado síncronamente"""
        sesion = self.obtener_o_crear_sesion(user_id)
        estado_actual = sesion["estado"]
        user_input = user_input.strip()

        # Comando global de escape para reiniciar el flujo
        if user_input.lower() in ["hola", "menu", "menú"]:
            sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
            return "MENU_PRINCIPAL"

        # =================================================================
        # EVALUACIÓN DE LA MÁQUINA DE ESTADOS
        # =================================================================
        
        # CASO 1: El usuario está en el Menú Principal
        if estado_actual == self.ESTADO_MENU_PRINCIPAL:
            if user_input == "1":
                sesion["estado"] = self.ESTADO_CATALOGO
                sesion["tienda_actual"] = self.DB_PASTELERIA # Asigna base de datos de Pastelería
                return "VISTA_CATALOGO"
            elif user_input == "2":
                sesion["estado"] = self.ESTADO_CATALOGO
                sesion["tienda_actual"] = self.DB_VIDEOJUEGOS # Asigna base de datos de Videojuegos
                return "VISTA_CATALOGO"
            elif user_input == "3":
                sesion["estado"] = self.ESTADO_CARRITO
                return "VISTA_CARRITO"
            elif user_input == "4":
                sesion["estado"] = self.ESTADO_SOPORTE
                return "MENU_SOPORTE"
            else:
                return self.control_fallback(estado_actual)

        # CASO 2: El usuario está explorando el Catálogo
        elif estado_actual == self.ESTADO_CATALOGO:
            if user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return "MENU_PRINCIPAL"
                
            # Si digita cualquier otra cosa, asumimos que intenta seleccionar un ID de Producto
            else:
                # CONEXIÓN REAL CON ELIAS:
                # Llamamos a su función 'verificar_stock' pasando la ruta dinámica y el ID que ingresó el usuario
                ruta_db = sesion["tienda_actual"]
                # Intentamos convertir la entrada a número por si el JSON usa enteros
                try:
                    id_convertido = int(user_input)
                except ValueError:
                    id_convertido = user_input # Si metió letras, lo dejamos como texto
                stock_disponible = database.verificar_stock(archivo_ruta=ruta_db, producto_id=user_input, cantidad_solicitada=1)
                
                if stock_disponible:
                    # ANCLAJE WILLIAM: Aquí el carrito sumará el producto en memoria más adelante
                    return "PRODUCTO_AGREGADO_EXITO" 
                else:
                    # Estrategia Z: Mitigación por falta de stock. Retorna alerta pero lo mantiene en el catálogo
                    print(f"[LOG CONTROL]: Bloqueo de transacción. Producto {user_input} sin stock en {ruta_db}.")
                    return "ALERTA_SIN_STOCK_REDIRECCION"

        # CASO 3: El usuario está revisando su Carrito de Compras
        elif estado_actual == self.ESTADO_CARRITO:
            if user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return "MENU_PRINCIPAL"
            elif user_input == "1":
                # ANCLAJE WILLIAM: Procesar el pago
                # ANCLAJE ELIAS (Futuro): Aquí se llamará a database.actualizar_stock() cuando el pago sea exitoso
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL 
                return "PROCESANDO_PAGO_FINALIZADO"
            elif user_input == "2":
                return "CARRITO_VACIADO_EXITO"
            else:
                return self.control_fallback(estado_actual)

        # CASO 4: El usuario está en el Módulo de Soporte
        elif estado_actual == self.ESTADO_SOPORTE:
            if user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return "MENU_PRINCIPAL"
            elif user_input == "1":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return "TICKET_SOPORTE_CREADO"
            else:
                return self.control_fallback(estado_actual)

    def control_fallback(self, estado_contexto: str) -> str:
        """Módulo de Mitigación de Errores: Evita que entradas inválidas rompan la app"""
        print(f"[FALLBACK LOG] Error de sintaxis capturado en el estado: {estado_contexto}")
        return f"FALLBACK_ERROR_{estado_contexto}"