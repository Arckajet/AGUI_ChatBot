# CÓDIGO DE WILLIAM (Lógica del carrito y cálculos de precios)

# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - MÓDULO DEL CARRITO LÓGICO
# DESARROLLADOR: WILLIAM RODRIGUEZ
# FASE 4 - ESTABILIZACIÓN DEL BACKEND (PERSISTENCIA)
# =====================================================================

import json
import os

TARIFA_DELIVERY = 3.00

# Ruta del archivo donde se persisten los carritos de todos los usuarios.
# Relativa a la raíz del proyecto (igual convención que soporte.RUTA_INCIDENCIAS).
# Si algún módulo necesita apuntar a una ruta absoluta (como hace estados.py
# con soporte.RUTA_INCIDENCIAS), puede sobreescribir carrito.RUTA_CARRITOS
# antes de la primera operación.
RUTA_CARRITOS = "data/carritos.json"

# Memoria temporal del carrito por sesión
# Estructura: {"user_id": [{"id": "P01", "nombre": "...", "precio": 15.0, "cantidad": 1}]}
carritos = {}


# =====================================================================
# FASE 4 — PERSISTENCIA DEL CARRITO
# =====================================================================
# Antes, `carritos` era un diccionario 100% en memoria: si el proceso de
# FastAPI se caía o se reiniciaba (deploy, crash, reinicio del servidor),
# todos los carritos de todos los usuarios se perdían sin aviso.
#
# Estrategia "write-through": cada función que modifica el carrito de un
# usuario (agregar_producto, vaciar_carrito, confirmar_compra) llama a
# guardar_carritos_en_json() al final. Así el archivo en disco nunca queda
# desactualizado por más de una operación. Al iniciar el módulo, se llama
# automáticamente a cargar_carritos_desde_json() para restaurar el último
# estado conocido.

def guardar_carritos_en_json():
    """
    Persiste el diccionario completo de carritos en disco.

    Se invoca automáticamente después de cada operación que modifica un
    carrito, para que un reinicio o caída del bot no le borre al usuario
    lo que ya tenía agregado.
    """
    try:
        carpeta = os.path.dirname(RUTA_CARRITOS)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(RUTA_CARRITOS, "w", encoding="utf-8") as f:
            json.dump(carritos, f, ensure_ascii=False, indent=4)
    except OSError as e:
        # No queremos que un fallo de disco tumbe la conversación del
        # usuario: solo se registra el error y el bot sigue funcionando
        # en memoria para esa sesión.
        print(f"[ERROR CARRITO] No se pudo guardar carritos.json: {e}")


def cargar_carritos_desde_json():
    """
    Carga los carritos guardados en disco al iniciar el módulo, para
    restaurar el estado de todos los usuarios tras un reinicio del bot.

    Si el archivo no existe todavía (primera vez que corre el bot) o está
    corrupto, arranca con carritos vacíos en lugar de tumbar el servidor.
    """
    global carritos
    if not os.path.exists(RUTA_CARRITOS):
        return
    try:
        with open(RUTA_CARRITOS, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            carritos = datos
            print(f"[CARRITO] {len(carritos)} carrito(s) restaurado(s) desde {RUTA_CARRITOS}")
    except (json.JSONDecodeError, OSError) as e:
        print(f"[ERROR CARRITO] No se pudo leer carritos.json, se arranca vacío: {e}")
        carritos = {}


def inicializar_carrito(user_id: str):
    """Inicializa un carrito vacío para el usuario si no existe."""
    if user_id not in carritos:
        carritos[user_id] = []


def agregar_producto(user_id: str, producto: dict) -> str:
    """
    Añade un producto al carrito del usuario.
    Si el producto ya existe, incrementa la cantidad.
    Recibe un dict con: id, nombre, precio
    Retorna confirmación de éxito.
    """
    inicializar_carrito(user_id)

    # Verificar si el producto ya está en el carrito
    for item in carritos[user_id]:
        if item["id"] == producto["id"]:
            item["cantidad"] += 1
            guardar_carritos_en_json()
            return f"✅ Se agregó otra unidad de *{producto['nombre']}* a tu carrito."

    # Si no existe, agregarlo con cantidad 1
    carritos[user_id].append({
        "id": producto["id"],
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": 1
    })
    guardar_carritos_en_json()
    return f"✅ *{producto['nombre']}* agregado al carrito por *${producto['precio']:.2f}*."


def vaciar_carrito(user_id: str) -> str:
    """Vacía completamente el carrito del usuario y persiste el cambio."""
    carritos[user_id] = []
    guardar_carritos_en_json()
    return "🗑️ Tu carrito ha sido vaciado. Escribe *Menu* para volver al inicio."


def calcular_total(user_id: str) -> dict:
    """
    Calcula subtotal, delivery y total del carrito.
    Retorna un dict con los valores calculados.
    """
    inicializar_carrito(user_id)
    subtotal = 0.0

    for item in carritos[user_id]:
        subtotal += item["precio"] * item["cantidad"]

    delivery = TARIFA_DELIVERY if subtotal > 0 else 0.0
    total = subtotal + delivery

    return {
        "subtotal": round(subtotal, 2),
        "delivery": round(delivery, 2),
        "total": round(total, 2)
    }


def ver_carrito(user_id: str) -> str:
    """
    Genera la factura digital en texto plano para mostrar al usuario.
    Formato compatible con WhatsApp y Telegram.
    """
    inicializar_carrito(user_id)

    if not carritos[user_id]:
        return (
            "🛒 Tu carrito está vacío.\n\n"
            "Escribe *1* para ver el catálogo o *Menu* para volver al inicio."
        )

    totales = calcular_total(user_id)
    lineas = ["🛒 *TU CARRITO*\n" + "─" * 30]

    for item in carritos[user_id]:
        subtotal_item = item["precio"] * item["cantidad"]
        lineas.append(f"{item['cantidad']}x {item['nombre']}  ${subtotal_item:.2f}")

    lineas.append("─" * 30)
    lineas.append(f"Subtotal:          ${totales['subtotal']:.2f}")
    lineas.append(f"Envío (Delivery):  ${totales['delivery']:.2f}")
    lineas.append(f"*TOTAL ESTIMADO:   ${totales['total']:.2f}*")
    lineas.append("\nEscribe el número de tu acción:")
    lineas.append("1. Confirmar Compra")
    lineas.append("2. Vaciar Carrito")
    lineas.append("0. Volver al Menú Principal")

    return "\n".join(lineas)


def confirmar_compra(user_id: str) -> str:
    """
    Procesa la confirmación de compra.
    Muestra el resumen final y limpia el carrito (con persistencia).
    """
    inicializar_carrito(user_id)

    if not carritos[user_id]:
        return "⚠️ No tienes productos en el carrito para confirmar."

    totales = calcular_total(user_id)
    resumen = ver_carrito(user_id)

    # Limpiar carrito tras confirmar (vaciar_carrito ya persiste el cambio)
    vaciar_carrito(user_id)

    return (
        f"✅ *¡Pedido confirmado con éxito!*\n\n"
        f"💰 Total cobrado: *${totales['total']:.2f}*\n\n"
        f"Un agente se pondrá en contacto contigo para coordinar el pago.\n"
        f"Escribe *Menu* para volver al inicio."
    )


# Restaurar carritos guardados apenas se importa este módulo, para que
# el estado sobreviva a reinicios del proceso de FastAPI.
cargar_carritos_desde_json()
