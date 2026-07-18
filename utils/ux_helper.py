# -- coding: utf-8 --


class UXHelper:
    """
    Clase encargada de la Experiencia de Usuario (UX) y adaptación de formatos
    para la interfaz móvil de WhatsApp.
    """

    @staticmethod
    def format_header(title: str) -> str:
        """Genera un encabezado llamativo pero compacto con emojis."""
        return f"✨ {title.upper()} ✨\n" + "─" * 20 + "\n"

    @staticmethod
    def format_menu(options: list) -> str:
        """
        Toma una lista de opciones y las formatea como una lista numerada limpia,
        ideal para que el usuario responda con un número en WhatsApp.
        """
        menu_text = ""
        for i, option in enumerate(options, 1):
            menu_text += f"{i}️⃣ {option}\n"
        return menu_text

    @staticmethod
    def get_user_manual() -> str:
        """
        Devuelve el manual de uso en formato optimizado para WhatsApp.
        Diseñado para ser enviado cuando el usuario escribe /ayuda o 'ayuda'.
        """
        manual = (
            f"{UXHelper.format_header('Guía de Uso Rápido')}"
            "¡Hola! Soy tu asistente virtual. 🤖\n"
            "Aquí tienes los comandos que puedes usar:\n\n"

            "📌 COMANDOS PRINCIPALES:\n"
            "🔹 1 o [Servicios] ➔ Ver lo que ofrecemos.\n"
            "🔹 2 o [Soporte] ➔ Contactar con un humano.\n"
            "🔹 3 o [Preguntas] ➔ Dudas frecuentes.\n"
            "🔹 /ayuda ➔ Ver este manual de nuevo.\n\n"

            "💡 Tip de uso: "
            "Para navegar más rápido, solo respóndeme con el número de la opción que desees. 📲\n\n"
            "_"
            "¿En qué te puedo colaborar hoy? Escribe tu opción abajo._"
        )
        return manual

    @staticmethod
    def format_error(message: str) -> str:
        """Formatea un mensaje de error de manera amigable y visual."""
        return f"⚠️ ¡Ups! Ocurrió un inconveniente\n\n{message}\n\n👉 Inténtalo de nuevo o escribe /ayuda."

    @staticmethod
    def format_success(message: str) -> str:
        """Formatea un mensaje de confirmación o éxito."""
        return f"✅ ¡Hecho!\n\n{message}"


# ==========================================
# PRUEBA LOCAL DEL MÓDULO (Para ver cómo luce)
# ==========================================
if __name__ == "__main__":
    # Esta sección solo se ejecuta si corres este archivo directamente.
    # Sirve para que Roberto verifique la visualización antes de integrarlo.

    print("--- VISTA PREVIA DEL MANUAL EN MÓVIL ---\n")
    print(UXHelper.get_user_manual())
    print("\n" + "="*40 + "\n")

    print("--- VISTA PREVIA DE UN MENÚ DE OPCIONES ---\n")
    opciones = ["Ver mi saldo", "Pagar factura", "Hablar con un asesor"]
    menu_bonito = UXHelper.format_header("Menú Principal") + UXHelper.format_menu(opciones)
    print(menu_bonito)