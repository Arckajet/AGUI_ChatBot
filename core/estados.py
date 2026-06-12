import sys
import os

# Agregamos la carpeta raíz del proyecto al camino de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data import database  # Módulo de Elias
import interfaz            # Módulo de Roberto
import carrito             # Módulo de William
import soporte             # Módulo de Eliezer

class MaquinaEstadosAGUI:
    def __init__(self):
        # Memoria de sesiones de usuarios para estados
        self.sesiones = {}
        
        # Estados Finitos de la CUI
        self.ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"
        self.ESTADO_CATALOGO = "VISTA_CATALOGO"
        self.ESTADO_CARRITO = "VISTA_CARRITO"
        self.ESTADO_SOPORTE = "MENU_SOPORTE"
        self.ESTADO_REGISTRANDO_INCIDENCIA = "REGISTRANDO_INCIDENCIA"
        
        # Solución de rutas absolutas robustas utilizando la ubicación de este archivo
        carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        self.DB_PASTELERIA = os.path.abspath(os.path.join(carpeta_actual, "..", "data", "inventario_pasteleria.json"))
        self.DB_VIDEOJUEGOS = os.path.abspath(os.path.join(carpeta_actual, "..", "data", "inventario_videojuegos.json"))
        
        # Sincronizamos la ruta de incidencias de Eliezer para que apunte bien a data/
        soporte.RUTA_INCIDENCIAS = os.path.abspath(os.path.join(carpeta_actual, "..", "data", "incidencias.json"))

    def obtener_o_crear_sesion(self, user_id: str) -> dict:
        if user_id not in self.sesiones:
            self.sesiones[user_id] = {
                "estado": self.ESTADO_MENU_PRINCIPAL,
                "tienda_actual": self.DB_PASTELERIA
            }
        return self.sesiones[user_id]

    def procesar_transicion(self, user_id: str, user_input: str) -> str:
        sesion = self.obtener_o_crear_sesion(user_id)
        estado_actual = sesion["estado"]
        user_input = user_input.strip()

        # =================================================================
        # INTERCEPTOR DE COMANDO SECRETO ADMIN (ELIEZER)
        # =================================================================
        if user_input.startswith("##admin"):
            ruta_db = sesion["tienda_actual"]
            inventario_crudo = database.leer_inventario(ruta_db)
            lista_productos = inventario_crudo.get("productos", [])
            
            # Eliezer procesa, valida el string y guarda en el JSON correspondiente
            resultado_admin = soporte.procesar_comando_admin(user_input, lista_productos, ruta_db)
            return resultado_admin

        # Comando de escape global
        if user_input.lower() in ["hola", "menu", "menú"]:
            sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
            return interfaz.mostrar_bienvenida()

        # =================================================================
        # EVALUACIÓN DE LA MÁQUINA DE ESTADOS MULTI-MÓDULO
        # =================================================================
        
        # CASO 1: Menú Principal
        if estado_actual == self.ESTADO_MENU_PRINCIPAL:
            if user_input == "1":
                sesion["estado"] = self.ESTADO_CATALOGO
                sesion["tienda_actual"] = self.DB_PASTELERIA
                datos_crudos = database.leer_inventario(self.DB_PASTELERIA)
                lista_final = datos_crudos.get("productos", []) if isinstance(datos_crudos, dict) else datos_crudos
                return interfaz.mostrar_menu_productos("Pastelería", lista_final)
                
            elif user_input == "2":
                sesion["estado"] = self.ESTADO_CATALOGO
                sesion["tienda_actual"] = self.DB_VIDEOJUEGOS
                datos_crudos = database.leer_inventario(self.DB_VIDEOJUEGOS)
                lista_final = datos_crudos.get("productos", []) if isinstance(datos_crudos, dict) else datos_crudos
                return interfaz.mostrar_menu_productos("Videojuegos", lista_final)
                
            elif user_input == "3":
                sesion["estado"] = self.ESTADO_CARRITO
                return carrito.ver_carrito(user_id)
                
            elif user_input == "4":
                sesion["estado"] = self.ESTADO_SOPORTE
                return soporte.menu_soporte() # Menú numérico de Eliezer
                
            elif user_input == "0":
                return "👋 ¡Gracias por usar AGUI Chatbot! Hasta luego."
            else:
                return self.control_fallback(estado_actual)

        # CASO 2: Catálogo de Productos
        elif estado_actual == self.ESTADO_CATALOGO:
            if user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return interfaz.mostrar_bienvenida()
            else:
                ruta_db = sesion["tienda_actual"]
                stock_disponible = database.verificar_stock(archivo_ruta=ruta_db, producto_id=user_input, cantidad_solicitada=1)
                
                if stock_disponible:
                    inventario = database.leer_inventario(ruta_db)
                    producto_encontrado = None
                    for prod in inventario.get("productos", []):
                        if str(prod["id"]) == user_input:
                            producto_encontrado = prod.copy()
                            break
                    
                    if producto_encontrado:
                        # Inyección de prefijos para evitar colisión de IDs en el carrito (Ángel Fix)
                        prefix = "PAST_" if "pasteleria" in ruta_db.lower() else "VIDEO_"
                        producto_encontrado["id"] = f"{prefix}{user_input}"
                        
                        msg_carrito = carrito.agregar_producto(user_id, producto_encontrado)
                        return msg_carrito + "\n\n💡 _Puedes seguir agregando IDs, marcar 0 para volver al menú principal._"
                    else:
                        return "❌ Error inesperado al procesar el producto."
                else:
                    return f"❌ Lo siento, el producto ID '{user_input}' no está disponible o no existe."

        # CASO 3: Carrito de Compras
        elif estado_actual == self.ESTADO_CARRITO:
            if user_input == "1":
                resumen_compra = carrito.confirmar_compra(user_id)
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return resumen_compra
            elif user_input == "2":
                msg_vaciado = carrito.vaciar_carrito(user_id)
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return msg_vaciado
            elif user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return interfaz.mostrar_bienvenida()
            else:
                return self.control_fallback(estado_actual)

        # CASO 4: Soporte Técnico (Gestión Numérica)
        elif estado_actual == self.ESTADO_SOPORTE:
            if user_input == "1":
                sesion["estado"] = self.ESTADO_REGISTRANDO_INCIDENCIA
                return interfaz.mostrar_soporte() # Plantilla estética de Roberto con los campos solicitados
            elif user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return interfaz.mostrar_bienvenida()
            else:
                return self.control_fallback(estado_actual)

        # CASO 5: Captura y escritura de la Incidencia física en JSON
        elif estado_actual == self.ESTADO_REGISTRANDO_INCIDENCIA:
            if user_input == "0":
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return interfaz.mostrar_bienvenida()
            
            # Tomamos todo el bloque de texto del usuario, Eliezer genera el ticket y guarda el JSON
            ticket_creado = soporte.crear_ticket(user_id, user_input)
            sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
            return ticket_creado + "\n\n" + interfaz.mostrar_bienvenida()

    def control_fallback(self, estado_contexto: str) -> str:
        return f"⚠️ Opción inválida para este menú. Por favor, intenta de nuevo."