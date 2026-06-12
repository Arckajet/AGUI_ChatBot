# CÓDIGO de Angel (Máquina de Estados Finitos y Fallbacks)

# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTERMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT (BACKEND CORE - MÁQUINA DE ESTADOS FINITOS)
# DESARROLLADOR: ÁNGEL (UX/UI DEVELOPER & CORE LOGIC)
# =====================================================================

class MaquinaEstadosAGUI:
    def __init__(self):
        # Memoria caché en servidor para persistencia de sesiones de usuarios
        # Estructura: {"numero_telefono": "ESTADO_ACTUAL"}
        self.sesiones = {}
        
        # Definición de los Estados Finitos de la CUI
        self.ESTADO_INACTIVO = "MENU_PRINCIPAL"
        self.ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"
        self.ESTADO_CATALOGO = "VISTA_CATALOGO"
        self.ESTADO_CARRITO = "VISTA_CARRITO"
        self.ESTADO_SOPORTE = "MENU_SOPORTE"

    def obtener_o_crear_sesion(self, user_id: str) -> str:
        """Módulo 0: Handshake - Recupera o inicializa el estado del cliente"""
        if user_id not in self.sesiones:
            self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL
            # ANCLAJE ELIAS: Aquí inicializarías el archivo JSON vacío del carrito para el usuario
        return self.sesiones[user_id]

    def procesar_transicion(self, user_id: str, user_input: str) -> str:
        """Cerebro del Bot: Evalúa la entrada y altera el estado síncronamente"""
        estado_actual = self.obtener_o_crear_sesion(user_id)
        user_input = user_input.strip()

        # Comando global de escape para mitigar fatiga cognitiva o reinicio
        if user_input.lower() in ["hola", "menu", "menú"]:
            self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL
            # ANCLAJE ROBERTO: Retorna la plantilla formateada del Menú Principal
            return "MENU_PRINCIPAL"

        # =================================================================
        # EVALUACIÓN DE LA MÁQUINA DE ESTADOS
        # =================================================================
        
        # CASO 1: El usuario está en el Menú Principal
        if estado_actual == self.ESTADO_MENU_PRINCIPAL:
            if user_input == "1":
                self.sesiones[user_id] = self.ESTADO_CATALOGO
                return "VISTA_CATALOGO"
            elif user_input == "2":
                self.sesiones[user_id] = self.ESTADO_CARRITO
                return "VISTA_CARRITO"
            elif user_input == "3":
                self.sesiones[user_id] = self.ESTADO_SOPORTE
                return "MENU_SOPORTE"
            else:
                # Dispara el sistema de mitigación de errores
                return self.control_fallback(estado_actual)

        # CASO 2: El usuario está explorando el Catálogo
        elif estado_actual == self.ESTADO_CATALOGO:
            # ANCLAJE ELIAS: Validar si el número ingresado corresponde a un ID de producto con Stock > 0
            if user_input == "0":
                self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL
                return "MENU_PRINCIPAL"
            elif user_input in ["1", "2", "3"]: # Simulador temporal de ítems del catálogo
                # BIFURCACIÓN CRÍTICA DE STOCK (REGLA: Si hay stock muestra Y, si no redirige a Z)
                stock_disponible = True # Cambiará al consumir la función de Elias
                
                if stock_disponible:
                    # ANCLAJE WILLIAM: Función para añadir producto seleccionado al carrito en memoria
                    # Permanece en catálogo por si desea seguir agregando ítems
                    return "PRODUCTO_AGREGADO_EXITO" 
                else:
                    # Redirección automática al catálogo limpiando el estado (Estrategia Z)
                    return "ALERTA_SIN_STOCK_REDIRECCION"
            else:
                return self.control_fallback(estado_actual)

        # CASO 3: El usuario está revisando su Carrito de Compras
        elif estado_actual == self.ESTADO_CARRITO:
            if user_input == "0":
                self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL
                return "MENU_PRINCIPAL"
            elif user_input == "1":
                # ANCLAJE WILLIAM: Procesar cálculos finales y pasar a datos de pago
                self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL # Resetea tras procesar orden
                return "PROCESANDO_PAGO_FINALIZADO"
            elif user_input == "2":
                # ANCLAJE WILLIAM: Vaciar el carrito de compras en la caché del servidor
                return "CARRITO_VACIADO_EXITO"
            else:
                return self.control_fallback(estado_actual)

        # CASO 4: El usuario está en el Módulo de Soporte / HelpDesk
        elif estado_actual == self.ESTADO_SOPORTE:
            if user_input == "0":
                self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL
                return "MENU_PRINCIPAL"
            elif user_input == "1":
                # ANCLAJE ELIEZER: Registrar descripción de falla y generar Ticket (TK-XXXX)
                self.sesiones[user_id] = self.ESTADO_MENU_PRINCIPAL # Restablece sesión al menú inicial
                return "TICKET_SOPORTE_CREADO"
            else:
                return self.control_fallback(estado_actual)

    def control_fallback(self, estado_contexto: str) -> str:
        """Módulo de Mitigación de Errores: Evita que entradas inválidas rompan la app"""
        # El estado del usuario no cambia, se retiene en el mismo punto para no perder su progreso
        print(f"[FALLBACK LOG] Error de sintaxis capturado en el estado: {estado_contexto}")
        
        # Retorna una etiqueta de control para que Roberto sepa qué mensaje de alerta estructurar
        return f"FALLBACK_ERROR_{estado_contexto}"