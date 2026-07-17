# CÓDIGO DE ELIEZER (Módulo de Soporte y Admin)

# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - MÓDULO DE SOPORTE Y ADMINISTRACIÓN
# DESARROLLADOR: WILLIAM RODRIGUEZ (en representación de Eliezer)
# FASE 4 - AUDITORÍA, ADMINISTRACIÓN Y REPORTES
# =====================================================================

import json
import random
import string
import os
from datetime import datetime, date

RUTA_INCIDENCIAS = "data/incidencias.json"
CLAVE_ADMIN = "##admin"
CLAVE_ADMIN_RESUELTO = "##admin_resuelto"
CLAVE_REPORTE = "##reporte"


def _generar_codigo_ticket() -> str:
    """Genera un código de ticket único alfanumérico. Ej: TK-9842"""
    numero = ''.join(random.choices(string.digits, k=4))
    return f"TK-{numero}"


def _cargar_incidencias() -> list:
    """Carga el archivo incidencias.json. Si no existe, retorna lista vacía."""
    if not os.path.exists(RUTA_INCIDENCIAS):
        return []
    with open(RUTA_INCIDENCIAS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _guardar_incidencias(incidencias: list):
    """Guarda la lista de incidencias en el archivo JSON."""
    with open(RUTA_INCIDENCIAS, "w", encoding="utf-8") as f:
        json.dump(incidencias, f, ensure_ascii=False, indent=4)


def crear_ticket(user_id: str, descripcion: str) -> str:
    """
    Genera un ticket de soporte único, lo registra en incidencias.json
    y retorna el mensaje de confirmación para el usuario.

    FASE 4: se agrega "fecha_creacion" (timestamp ISO) para poder
    calcular el reporte diario de incidencias abiertas/cerradas.
    """
    codigo = _generar_codigo_ticket()

    nuevo_ticket = {
        "ticket": codigo,
        "user_id": user_id,
        "descripcion": descripcion,
        "status": "Abierto",
        "prioridad": "Alta",
        "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
        "fecha_resolucion": None,
    }

    incidencias = _cargar_incidencias()
    incidencias.append(nuevo_ticket)
    _guardar_incidencias(incidencias)

    return (
        f"✅ Tu reporte ha sido registrado con éxito.\n\n"
        f"🎫 *CÓDIGO DE TICKET: {codigo}*\n"
        f"   Status: Abierto\n"
        f"   Prioridad: Alta\n\n"
        f"Un agente revisará tu caso a la brevedad y te contactará directamente.\n"
        f"Escribe *Menu* en cualquier momento para volver al inicio."
    )


def procesar_comando_admin(mensaje: str, inventario: list, ruta_inventario: str) -> str:
    """
    Valida el comando ##admin y permite agregar productos al inventario.
    Formato esperado: ##admin|ID|Nombre|Precio|Stock
    Ejemplo:          ##admin|P03|Tarta Red Velvet|18.0|5

    Nota Fase 4: este comando NO debe activarse si el mensaje en realidad
    es ##admin_resuelto|... — quien enruta los comandos (estados.py) ya
    revisa CLAVE_ADMIN_RESUELTO antes que CLAVE_ADMIN, pero se deja esta
    verificación aquí también como segunda capa de seguridad.
    """
    if not mensaje.startswith(CLAVE_ADMIN) or mensaje.startswith(CLAVE_ADMIN_RESUELTO):
        return None

    partes = mensaje.split("|")

    if len(partes) != 5:
        return (
            "⚠️ *Formato incorrecto.*\n"
            "Usa: ##admin|ID|Nombre|Precio|Stock\n"
            "Ejemplo: ##admin|P03|Tarta Red Velvet|18.0|5"
        )

    try:
        nuevo_producto = {
            "id": partes[1].strip(),
            "nombre": partes[2].strip(),
            "precio": float(partes[3].strip()),
            "stock": int(partes[4].strip())
        }
    except ValueError:
        return "⚠️ Error: El precio debe ser un número decimal y el stock un número entero."

    # Verificar si el ID ya existe
    for producto in inventario:
        if producto["id"] == nuevo_producto["id"]:
            return f"⚠️ Ya existe un producto con el ID *{nuevo_producto['id']}*."

    inventario.append(nuevo_producto)

    with open(ruta_inventario, "w", encoding="utf-8") as f:
        json.dump({"productos": inventario}, f, ensure_ascii=False, indent=4)

    return (
        f"✅ *Producto agregado exitosamente al inventario.*\n\n"
        f"🆔 ID: {nuevo_producto['id']}\n"
        f"📦 Nombre: {nuevo_producto['nombre']}\n"
        f"💲 Precio: ${nuevo_producto['precio']:.2f}\n"
        f"📊 Stock: {nuevo_producto['stock']} unidades"
    )


# =====================================================================
# FASE 4 — MÓDULO DE GESTIÓN DE TICKETS (ADMIN)
# =====================================================================
def resolver_ticket_admin(mensaje: str) -> str:
    """
    Permite a un administrador marcar un ticket como resuelto.
    Formato esperado: ##admin_resuelto|TK-XXXX
    Ejemplo:          ##admin_resuelto|TK-9842

    Actualiza el status a "Resuelto" y registra fecha_resolucion,
    que luego usa generar_reporte_diario() para contar cuántos
    tickets se cerraron hoy.
    """
    if not mensaje.startswith(CLAVE_ADMIN_RESUELTO):
        return None

    partes = mensaje.split("|")

    if len(partes) != 2 or not partes[1].strip():
        return (
            "⚠️ *Formato incorrecto.*\n"
            "Usa: ##admin_resuelto|TK-XXXX\n"
            "Ejemplo: ##admin_resuelto|TK-9842"
        )

    codigo_buscado = partes[1].strip().upper()
    incidencias = _cargar_incidencias()

    for ticket in incidencias:
        if ticket.get("ticket", "").upper() == codigo_buscado:
            if ticket.get("status") == "Resuelto":
                return f"ℹ️ El ticket *{codigo_buscado}* ya estaba marcado como Resuelto."

            ticket["status"] = "Resuelto"
            ticket["fecha_resolucion"] = datetime.now().isoformat(timespec="seconds")
            _guardar_incidencias(incidencias)

            return (
                f"✅ *Ticket {codigo_buscado} marcado como Resuelto.*\n"
                f"Descripción original: {ticket.get('descripcion', 'N/A')}"
            )

    return f"⚠️ No se encontró ningún ticket con el código *{codigo_buscado}*."


# =====================================================================
# FASE 4 — REPORTE FINAL DE INCIDENCIAS
# =====================================================================
def generar_reporte_diario() -> str:
    """
    Genera un resumen automático de la actividad de soporte del día:
    cuántos tickets se abrieron hoy y cuántos se cerraron hoy.

    Se activa con el comando ##reporte (pensado para uso de administradores,
    mismo canal que ##admin y ##admin_resuelto).

    Tickets creados antes de la Fase 4 no tienen "fecha_creacion" — se
    ignoran para el conteo del día en vez de romper el reporte.
    """
    incidencias = _cargar_incidencias()
    hoy = date.today().isoformat()  # "YYYY-MM-DD"

    abiertos_hoy = 0
    cerrados_hoy = 0
    total_abiertos = 0

    for ticket in incidencias:
        fecha_creacion = (ticket.get("fecha_creacion") or "")[:10]
        fecha_resolucion = (ticket.get("fecha_resolucion") or "")[:10]

        if fecha_creacion == hoy:
            abiertos_hoy += 1
        if ticket.get("status") == "Resuelto" and fecha_resolucion == hoy:
            cerrados_hoy += 1
        if ticket.get("status") == "Abierto":
            total_abiertos += 1

    return (
        f"📊 *REPORTE DIARIO DE INCIDENCIAS*\n"
        f"Fecha: {hoy}\n"
        f"─────────────────────\n"
        f"Hoy se abrieron *{abiertos_hoy}* ticket(s) y se cerraron *{cerrados_hoy}*.\n\n"
        f"🔓 Tickets abiertos actualmente (histórico): {total_abiertos}\n"
        f"🗂️ Total de tickets registrados: {len(incidencias)}"
    )


def menu_soporte() -> str:
    """Retorna el mensaje del menú de soporte formateado."""
    return (
        "🛠️ *SOPORTE TÉCNICO*\n"
        "─────────────────────\n"
        "Describe tu problema y un agente te contactará.\n\n"
        "Escribe el número de tu acción:\n"
        "1. Reportar un problema\n"
        "0. Volver al Menú Principal"
    )
