# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - SCRIPT DE INICIALIZACIÓN Y CIERRE DE TICKETS
# DESARROLLADOR: WILLIAM RODRIGUEZ (en representación de Eliezer)
# FASE 3 - ADMINISTRADOR DEL SISTEMA Y REPORTES FINALES
# =====================================================================

import json
import os
from datetime import datetime


# ── Rutas de los archivos del sistema ────────────────────────────────
RUTA_DATA             = "data"
RUTA_INCIDENCIAS      = "data/incidencias.json"
RUTA_SESIONES         = "data/sesiones_usuario.json"
RUTA_INV_PASTELERIA   = "data/inventario_pasteleria.json"
RUTA_INV_VIDEOJUEGOS  = "data/inventario_videojuegos.json"


# ═══════════════════════════════════════════════════════════════════
# PARTE 1 — SCRIPT DE INICIALIZACIÓN
# Se ejecuta UNA VEZ antes de arrancar el servidor de William
# ═══════════════════════════════════════════════════════════════════

def verificar_carpeta_data():
    """Verifica que la carpeta data/ exista. Si no, la crea."""
    if not os.path.exists(RUTA_DATA):
        os.makedirs(RUTA_DATA)
        print(f"[INIT] Carpeta '{RUTA_DATA}/' creada.")
    else:
        print(f"[INIT] Carpeta '{RUTA_DATA}/' OK.")


def inicializar_archivo(ruta: str, contenido_default):
    """
    Verifica si un archivo JSON existe.
    Si no existe, lo crea con el contenido por defecto.
    Si existe pero está corrupto, lo reinicia.
    """
    if not os.path.exists(ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(contenido_default, f, ensure_ascii=False, indent=4)
        print(f"[INIT] Archivo '{ruta}' creado.")
    else:
        # Verificar que no esté corrupto
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                json.load(f)
            print(f"[INIT] Archivo '{ruta}' OK.")
        except json.JSONDecodeError:
            print(f"[INIT] Archivo '{ruta}' corrupto. Reiniciando...")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(contenido_default, f, ensure_ascii=False, indent=4)
            print(f"[INIT] Archivo '{ruta}' reiniciado.")


def inicializar_sistema():
    """
    Función principal de inicialización.
    William debe llamar esta función al arrancar el servidor FastAPI.
    Verifica que todas las carpetas y archivos necesarios existan.
    """
    print("\n" + "="*50)
    print("  AGUIBOT — Verificación del sistema")
    print("="*50)

    # 1. Verificar carpeta data/
    verificar_carpeta_data()

    # 2. Archivo de sesiones de usuarios (para Elias - persistencia)
    inicializar_archivo(RUTA_SESIONES, {})

    # 3. Archivo de incidencias/tickets de soporte
    inicializar_archivo(RUTA_INCIDENCIAS, [])

    # 4. Inventario de pastelería (si no lo creó Elias)
    inicializar_archivo(RUTA_INV_PASTELERIA, {
        "productos": [
            {"id": "P01", "nombre": "Pastel de Chocolate", "precio": 15.0, "stock": 5},
            {"id": "P02", "nombre": "Cupcake de Vainilla",  "precio": 2.5,  "stock": 0}
        ]
    })

    # 5. Inventario de videojuegos (si no lo creó Elias)
    inicializar_archivo(RUTA_INV_VIDEOJUEGOS, {
        "productos": [
            {"id": "V01", "nombre": "Grand Theft Auto 6", "precio": 60.0, "stock": 3},
            {"id": "V02", "nombre": "FIFA 26",            "precio": 70.0, "stock": 12}
        ]
    })

    print("="*50)
    print("  Sistema listo. Arrancando servidor...")
    print("="*50 + "\n")


# ═══════════════════════════════════════════════════════════════════
# PARTE 2 — MÓDULO DE CIERRE DE TICKETS
# Permite al administrador cambiar el estado de un ticket
# ═══════════════════════════════════════════════════════════════════

def _cargar_incidencias() -> list:
    """Carga el archivo de incidencias. Retorna lista vacía si no existe."""
    if not os.path.exists(RUTA_INCIDENCIAS):
        return []
    with open(RUTA_INCIDENCIAS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _guardar_incidencias(incidencias: list):
    """Guarda la lista de incidencias actualizada en el archivo."""
    with open(RUTA_INCIDENCIAS, "w", encoding="utf-8") as f:
        json.dump(incidencias, f, ensure_ascii=False, indent=4)


def cerrar_ticket(codigo_ticket: str, resolucion: str = "Problema resuelto") -> str:
    """
    Cambia el estado de un ticket de 'Abierto' a 'Resuelto'.

    Args:
        codigo_ticket: El código del ticket (ej. 'TK-9842')
        resolucion: Descripción de cómo se resolvió el problema

    Returns:
        Mensaje confirmando el cierre o indicando que no se encontró
    """
    incidencias = _cargar_incidencias()

    for ticket in incidencias:
        if ticket.get("ticket") == codigo_ticket:

            if ticket.get("status") == "Resuelto":
                return f"⚠️ El ticket {codigo_ticket} ya estaba marcado como Resuelto."

            # Actualizar el ticket
            ticket["status"]       = "Resuelto"
            ticket["resolucion"]   = resolucion
            ticket["fecha_cierre"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            _guardar_incidencias(incidencias)

            print(f"[ADMIN] Ticket {codigo_ticket} cerrado correctamente.")
            return (
                f"✅ *Ticket {codigo_ticket} cerrado.*\n\n"
                f"Estado: Resuelto\n"
                f"Resolucion: {resolucion}\n"
                f"Fecha de cierre: {ticket['fecha_cierre']}"
            )

    return f"❌ No se encontro ningun ticket con el codigo {codigo_ticket}."


def listar_tickets(solo_abiertos: bool = True) -> str:
    """
    Lista los tickets registrados en el sistema.

    Args:
        solo_abiertos: Si True, muestra solo los tickets con status 'Abierto'

    Returns:
        Texto formateado con la lista de tickets
    """
    incidencias = _cargar_incidencias()

    if not incidencias:
        return "📋 No hay tickets registrados en el sistema."

    if solo_abiertos:
        lista = [t for t in incidencias if t.get("status") == "Abierto"]
        titulo = "📋 *TICKETS ABIERTOS*"
    else:
        lista = incidencias
        titulo = "📋 *TODOS LOS TICKETS*"

    if not lista:
        return "✅ No hay tickets abiertos. Todo resuelto."

    lineas = [titulo, "─" * 30]
    for t in lista:
        lineas.append(
            f"🎫 {t.get('ticket')} | {t.get('status')}\n"
            f"   Usuario: {t.get('user_id')}\n"
            f"   Descripcion: {t.get('descripcion', 'Sin descripcion')}"
        )
        lineas.append("─" * 30)

    return "\n".join(lineas)


# ═══════════════════════════════════════════════════════════════════
# EJECUCIÓN DIRECTA — Para probar el inicializador manualmente
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Al ejecutar este archivo directamente, inicializa el sistema
    inicializar_sistema()

    # Prueba: listar tickets existentes
    print("\n--- Tickets en el sistema ---")
    print(listar_tickets(solo_abiertos=False))
