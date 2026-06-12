# CÓDIGO DE WILLIAM (Lógica del carrito y cálculos de precios)

# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - MÓDULO DEL CARRITO LÓGICO
# DESARROLLADOR: WILLIAM RODRIGUEZ
# =====================================================================

TARIFA_DELIVERY = 3.00

# Memoria temporal del carrito por sesión
# Estructura: {"user_id": [{"id": "P01", "nombre": "...", "precio": 15.0, "cantidad": 1}]}
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
            return f"✅ Se agregó otra unidad de *{producto['nombre']}* a tu carrito."

    # Si no existe, agregarlo con cantidad 1
    carritos[user_id].append({
        "id": producto["id"],
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": 1
    })
    return f"✅ *{producto['nombre']}* agregado al carrito por *${producto['precio']:.2f}*."


def vaciar_carrito(user_id: str) -> str:
    """Vacía completamente el carrito del usuario en memoria."""
    carritos[user_id] = []
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
    Muestra el resumen final y limpia el carrito.
    """
    inicializar_carrito(user_id)

    if not carritos[user_id]:
        return "⚠️ No tienes productos en el carrito para confirmar."

    totales = calcular_total(user_id)
    resumen = ver_carrito(user_id)

    # Limpiar carrito tras confirmar
    vaciar_carrito(user_id)

    return (
        f"✅ *¡Pedido confirmado con éxito!*\n\n"
        f"💰 Total cobrado: *${totales['total']:.2f}*\n\n"
        f"Un agente se pondrá en contacto contigo para coordinar el pago.\n"
        f"Escribe *Menu* para volver al inicio."
    )