# CÓDIGO DE ROBERTO (Formatos de texto, menús y emojis)
# =======================================================
# AGUI CHATBOT - INTERFAZ.PY (Diseño de Roberto)
# =======================================================

# --- CONSTANTES DE DISEÑO (Para mantener la armonía visual) ---
SEPARADOR_PRINCIPAL = "════════════════════════════════"
SEPARADOR_SECUNDARIO = "--------------------------------"
EMOJI_ITEM = "🔹"
EMOJI_PRECIO = "💰"

def mostrar_bienvenida() -> str:
    """
    Menú de bienvenida principal del chatbot AGUI.
    Mitiga la fatiga cognitiva ofreciendo opciones claras y numeradas.
    """
    return f"""
{SEPARADOR_PRINCIPAL}
🤖 ¡Hola! Bienvenido a **AGUI Chatbot** 🦅
{SEPARADOR_PRINCIPAL}
Estoy aquí para ayudarte. Por favor, selecciona una opción 
escribiendo el número correspondiente:

1️⃣  🍰 *Ver Pastelería*
2️⃣  🎮 *Ver Tienda de Videojuegos*
3️⃣  🛒 *Ver mi Carrito de Compras*
4️⃣  📞 *Hablar con Soporte*

❌ Escribe *0* para salir del chat.
{SEPARADOR_PRINCIPAL}
"""

def mostrar_menu_productos(categoria: str, lista_productos: list) -> str:
    """
    Diseña dinámicamente el menú de productos según la tienda seleccionada.
    Toma los datos crudos del JSON y los maqueta estéticamente.
    """
    # Cambia el emoji del título según la categoría
    icono = "🍰" if "past" in categoria.lower() else "🕹️"
    
    texto = f"\n{SEPARADOR_PRINCIPAL}\n"
    texto += f"{icono} **CATÁLOGO DE {categoria.upper()}** {icono}\n"
    texto += f"{SEPARADOR_PRINCIPAL}\n\n"
    
    # Recorre los productos que vengan del inventario JSON
    for i, prod in enumerate(lista_productos, 1):
        texto += f"{i}️⃣  {EMOJI_ITEM} *{prod['nombre']}*\n"
        texto += f"    └─ {EMOJI_PRECIO} Precio: ${prod['precio']}\n\n"
        
    texto += f"{SEPARADOR_SECUNDARIO}\n"
    texto += "0️⃣  ↩️ *Volver al menú principal*\n"
    texto += f"{SEPARADOR_PRINCIPAL}\n"
    return texto

def mostrar_soporte() -> str:
    """Diseño limpio para la sección de soporte técnico."""
    return f"""
{SEPARADOR_PRINCIPAL}
📞 **SOPORTE TÉCNICO**
{SEPARADOR_PRINCIPAL}
¿Tienes algún problema con tu pedido o el sistema? 

💡 _Déjanos tu mensaje detallado en el siguiente formato:_
• *Nombre:*
• *Cédula/ID:*
• *Descripción del problema:*

Un asesor humano te contactará lo más pronto posible.
{SEPARADOR_SECUNDARIO}
0️⃣  ↩️ *Volver al menú principal*
{SEPARADOR_PRINCIPAL}
"""