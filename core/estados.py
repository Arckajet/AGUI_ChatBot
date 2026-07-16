import sys
import os
import threading
import unicodedata

# =====================================================================
# PATH SETUP — Works from any entry point (main.py, test_bot.py, etc.)
# =====================================================================
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CORE_DIR, ".."))

for _path in (_PROJECT_ROOT, _CORE_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from data import database  # Módulo de Elias
import interfaz            # Módulo de Roberto
import carrito             # Módulo de William
import soporte             # Módulo de Eliezer


class MaquinaEstadosAGUI:
    """
    Finite State Machine (CUI) for AGUIBOT.

    Thread-safe: all session access is serialized through a coarse-grained lock.
    Each user_id (international phone number) gets an isolated session dict.
    The cart is managed externally by William's carrito module, keyed by user_id.
    """

    # ─── Finite states ───────────────────────────────────────────────
    ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"
    ESTADO_CATALOGO = "VISTA_CATALOGO"
    ESTADO_CARRITO = "VISTA_CARRITO"
    ESTADO_SOPORTE = "MENU_SOPORTE"
    ESTADO_REGISTRANDO_INCIDENCIA = "REGISTRANDO_INCIDENCIA"

    # ─── Global escape commands ──────────────────────────────────────
    _COMANDOS_GLOBALES = frozenset({"hola", "menu", "menú"})

    def __init__(self):
        # Per-user session store: {user_id: {estado, tienda_actual}}
        self.sesiones = {}

        # Coarse-grained lock — serializes access to self.sesiones so
        # concurrent FastAPI requests never corrupt session state
        self._lock = threading.Lock()

        # Absolute paths to inventory databases
        self.DB_PASTELERIA = os.path.abspath(
            os.path.join(_CORE_DIR, "..", "data", "inventario_pasteleria.json")
        )
        self.DB_VIDEOJUEGOS = os.path.abspath(
            os.path.join(_CORE_DIR, "..", "data", "inventario_videojuegos.json")
        )

        # Sync Eliezer's incident path to data/
        soporte.RUTA_INCIDENCIAS = os.path.abspath(
            os.path.join(_CORE_DIR, "..", "data", "incidencias.json")
        )

        # FASE 4 — Sync William's cart persistence path to data/, misma
        # convención que ya se usaba para soporte.RUTA_INCIDENCIAS.
        carrito.RUTA_CARRITOS = os.path.abspath(
            os.path.join(_CORE_DIR, "..", "data", "carritos.json")
        )
        # Como carrito.py ya cargó los carritos al importarse (con la ruta
        # relativa por defecto), se vuelve a cargar aquí una vez fijada la
        # ruta absoluta correcta, para no perder lo que ya hubiera en disco.
        carrito.cargar_carritos_desde_json()

    # =================================================================
    # PRIVATE HELPERS
    # =================================================================

    @staticmethod
    def _sanitizar_input(raw_input):
        """
        Validate and clean raw user input from WhatsApp webhook payloads.

        Returns:
            tuple: (cleaned_text, None) on success,
                   (None, error_message) if input is invalid.
        """
        # Reject non-string types (images, stickers, voice notes, location
        # pins, etc. arrive as dicts/bytes in webhook payloads)
        if not isinstance(raw_input, str):
            return None, (
                "⚠️ Solo acepto comandos de texto.\n"
                "Por favor, escribe un número o una palabra para continuar."
            )

        # Normalize Unicode (mobile keyboards can send decomposed chars)
        cleaned = unicodedata.normalize("NFC", raw_input).strip()

        # Reject empty or whitespace-only input
        if not cleaned:
            return None, (
                "⚠️ No recibí ningún texto.\n"
                "Por favor, escribe una opción válida para continuar."
            )

        # Reject strings with only non-printable / control characters
        if not any(c.isprintable() and not c.isspace() for c in cleaned):
            return None, (
                "⚠️ Solo acepto comandos de texto.\n"
                "Por favor, escribe un número o una palabra para continuar."
            )

        return cleaned, None

    def _es_comando_global(self, texto_lower):
        """Check if the lowercased input is a global escape command."""
        return texto_lower in self._COMANDOS_GLOBALES

    def _resetear_sesion_a_menu(self, sesion):
        """
        Reset session to main menu state.

        Clears intermediate navigation state (current store, etc.) but
        does NOT touch the shopping cart — that's managed independently
        by William's carrito module, keyed by user_id.
        """
        sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
        sesion["tienda_actual"] = self.DB_PASTELERIA

    # =================================================================
    # PUBLIC API
    # =================================================================

    def obtener_o_crear_sesion(self, user_id):
        """Get or create an isolated session for the given user_id."""
        if user_id not in self.sesiones:
            self.sesiones[user_id] = {
                "estado": self.ESTADO_MENU_PRINCIPAL,
                "tienda_actual": self.DB_PASTELERIA,
            }
        return self.sesiones[user_id]

    def procesar_transicion(self, user_id, user_input):
        """
        Main FSM entry point. Processes a user message and returns
        the bot's response string.

        Thread-safe: serializes all session access through a lock.

        Args:
            user_id: International phone number (e.g. "+584121234567").
            user_input: Raw input from the webhook payload. May be None,
                        non-str, empty, or contain non-printable chars.

        Returns:
            Formatted response string for WhatsApp.
        """
        # ─── STEP 0: Input sanitization (before any state access) ────
        cleaned, error_msg = self._sanitizar_input(user_input)
        if error_msg is not None:
            return error_msg

        # From here on, `cleaned` is a guaranteed non-empty, normalized string
        with self._lock:
            sesion = self.obtener_o_crear_sesion(user_id)
            estado_actual = sesion["estado"]

            # ─── INTERCEPTOR: Admin — cerrar ticket (Eliezer, Fase 4) ─
            # OJO: debe revisarse ANTES que "##admin" a secas, porque
            # "##admin_resuelto" también empieza con el prefijo "##admin".
            if cleaned.startswith("##admin_resuelto"):
                return soporte.resolver_ticket_admin(cleaned)

            # ─── INTERCEPTOR: Admin — reporte diario (Eliezer, Fase 4) ─
            if cleaned.startswith("##reporte"):
                return soporte.generar_reporte_diario()

            # ─── INTERCEPTOR: Admin command (Eliezer) ────────────
            if cleaned.startswith("##admin"):
                ruta_db = sesion["tienda_actual"]
                inventario_crudo = database.leer_inventario(ruta_db)
                lista_productos = inventario_crudo.get("productos", [])
                return soporte.procesar_comando_admin(
                    cleaned, lista_productos, ruta_db
                )

            # ─── INTERCEPTOR: Global escape commands ─────────────
            # "hola", "menu", "menú" → clean state, preserve cart,
            # return to main menu with Roberto's welcome screen
            if self._es_comando_global(cleaned.lower()):
                self._resetear_sesion_a_menu(sesion)
                return interfaz.mostrar_bienvenida()

            # ==========================================================
            # FINITE STATE MACHINE — MULTI-MODULE EVALUATION
            # ==========================================================

            # CASE 1: Main Menu
            if estado_actual == self.ESTADO_MENU_PRINCIPAL:
                if cleaned == "1":
                    sesion["estado"] = self.ESTADO_CATALOGO
                    sesion["tienda_actual"] = self.DB_PASTELERIA
                    datos_crudos = database.leer_inventario(self.DB_PASTELERIA)
                    lista_final = (
                        datos_crudos.get("productos", [])
                        if isinstance(datos_crudos, dict)
                        else datos_crudos
                    )
                    return interfaz.mostrar_menu_productos("Pastelería", lista_final)

                elif cleaned == "2":
                    sesion["estado"] = self.ESTADO_CATALOGO
                    sesion["tienda_actual"] = self.DB_VIDEOJUEGOS
                    datos_crudos = database.leer_inventario(self.DB_VIDEOJUEGOS)
                    lista_final = (
                        datos_crudos.get("productos", [])
                        if isinstance(datos_crudos, dict)
                        else datos_crudos
                    )
                    return interfaz.mostrar_menu_productos("Videojuegos", lista_final)

                elif cleaned == "3":
                    sesion["estado"] = self.ESTADO_CARRITO
                    return carrito.ver_carrito(user_id)

                elif cleaned == "4":
                    sesion["estado"] = self.ESTADO_SOPORTE
                    return soporte.menu_soporte()

                elif cleaned == "0":
                    return "👋 ¡Gracias por usar AGUI Chatbot! Hasta luego."

                else:
                    return self.control_fallback(estado_actual)

            # CASE 2: Product Catalog
            elif estado_actual == self.ESTADO_CATALOGO:
                if cleaned == "0":
                    sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                    return interfaz.mostrar_bienvenida()
                else:
                    ruta_db = sesion["tienda_actual"]
                    stock_disponible = database.verificar_stock(
                        archivo_ruta=ruta_db,
                        producto_id=cleaned,
                        cantidad_solicitada=1,
                    )

                    if stock_disponible:
                        inventario = database.leer_inventario(ruta_db)
                        producto_encontrado = None
                        for prod in inventario.get("productos", []):
                            if str(prod["id"]) == cleaned:
                                producto_encontrado = prod.copy()
                                break

                        if producto_encontrado:
                            # ID prefix injection to avoid cart collisions (Ángel Fix)
                            prefix = (
                                "PAST_"
                                if "pasteleria" in ruta_db.lower()
                                else "VIDEO_"
                            )
                            producto_encontrado["id"] = f"{prefix}{cleaned}"

                            msg_carrito = carrito.agregar_producto(
                                user_id, producto_encontrado
                            )
                            return (
                                msg_carrito
                                + "\n\n💡 _Puedes seguir agregando IDs, "
                                "marca 0 para volver al menú principal._"
                            )
                        else:
                            return "❌ Error inesperado al procesar el producto."
                    else:
                        return (
                            f"❌ Lo siento, el producto ID '{cleaned}' "
                            "no está disponible o no existe."
                        )

            # CASE 3: Shopping Cart
            elif estado_actual == self.ESTADO_CARRITO:
                if cleaned == "1":
                    resumen_compra = carrito.confirmar_compra(user_id)
                    sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                    return resumen_compra
                elif cleaned == "2":
                    msg_vaciado = carrito.vaciar_carrito(user_id)
                    sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                    return msg_vaciado
                elif cleaned == "0":
                    sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                    return interfaz.mostrar_bienvenida()
                else:
                    return self.control_fallback(estado_actual)

            # CASE 4: Technical Support (numeric menu)
            elif estado_actual == self.ESTADO_SOPORTE:
                if cleaned == "1":
                    sesion["estado"] = self.ESTADO_REGISTRANDO_INCIDENCIA
                    return interfaz.mostrar_soporte()
                elif cleaned == "0":
                    sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                    return interfaz.mostrar_bienvenida()
                else:
                    return self.control_fallback(estado_actual)

            # CASE 5: Incident Registration (free-text capture)
            elif estado_actual == self.ESTADO_REGISTRANDO_INCIDENCIA:
                if cleaned == "0":
                    sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                    return interfaz.mostrar_bienvenida()

                # Eliezer generates the ticket and persists to JSON
                ticket_creado = soporte.crear_ticket(user_id, cleaned)
                sesion["estado"] = self.ESTADO_MENU_PRINCIPAL
                return ticket_creado + "\n\n" + interfaz.mostrar_bienvenida()

            # ─── SAFETY NET: Unknown/corrupted state ─────────────
            else:
                self._resetear_sesion_a_menu(sesion)
                return (
                    "⚠️ Ocurrió un error inesperado en la sesión.\n"
                    "Te he devuelto al menú principal.\n\n"
                    + interfaz.mostrar_bienvenida()
                )

    def control_fallback(self, estado_contexto):
        """
        Context-aware fallback for invalid user input.
        Returns a guidance message specific to the current FSM state.
        """
        guias = {
            self.ESTADO_MENU_PRINCIPAL: (
                "Escribe un número del *1 al 4*, o *0* para salir."
            ),
            self.ESTADO_CATALOGO: (
                "Escribe el *ID del producto* que deseas agregar, o *0* para volver."
            ),
            self.ESTADO_CARRITO: (
                "Escribe *1* para confirmar, *2* para vaciar, o *0* para volver."
            ),
            self.ESTADO_SOPORTE: (
                "Escribe *1* para reportar un problema, o *0* para volver."
            ),
            self.ESTADO_REGISTRANDO_INCIDENCIA: (
                "Escribe tu reporte o *0* para volver al menú."
            ),
        }
        guia = guias.get(estado_contexto, "Escribe *menu* para volver al inicio.")
        return f"⚠️ Opción inválida. {guia}"
