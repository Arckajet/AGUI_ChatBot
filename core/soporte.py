# CÓDIGO DE ELIEZER (Módulo de Soporte y Admin)

# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - MÓDULO DE SOPORTE Y ADMINISTRACIÓN
# DESARROLLADOR: WILLIAM RODRIGUEZ (en representación de Eliezer)
# =====================================================================

import json
import random
import string
import os

RUTA_INCIDENCIAS = "data/incidencias.json"
CLAVE_ADMIN = "##admin"


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
    """
    codigo = _generar_codigo_ticket()

    nuevo_ticket = {
        "ticket": codigo,
        "user_id": user_id,
        "descripcion": descripcion,
        "status": "Abierto",
        "prioridad": "Alta"
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
    """
    if not mensaje.startswith(CLAVE_ADMIN):
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