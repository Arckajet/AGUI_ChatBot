# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - SERVIDOR FASTAPI (WEBHOOK)
# DESARROLLADOR: WILLIAM RODRIGUEZ
# FASE 4 - ESTABILIZACIÓN DEL BACKEND (CONCURRENCIA Y ERRORES HTTP)
# =====================================================================

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import httpx
import os

# Importar el cerebro del bot (Ángel)
from estados import MaquinaEstadosAGUI

# ── Inicializar la app y la máquina de estados ──────────────────────
app = FastAPI(
    title="AGUIBot API",
    description="Backend del asistente de autoatención AGUI",
    version="2.1.0"
)

# Una sola instancia de la máquina compartida por todos los usuarios
maquina = MaquinaEstadosAGUI()

# ── Credenciales Twilio (se leen desde variables de entorno) ─────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Mensaje de error genérico pedido en la guía de Fase 4
MENSAJE_ERROR_USUARIO = "⚠️ Error, intenta de nuevo. Escribe *Menu* para reiniciar."


# ── Función auxiliar: enviar mensaje de vuelta a WhatsApp ────────────
async def enviar_mensaje_whatsapp(numero_destino: str, mensaje: str):
    """
    Envía un mensaje de texto al cliente via Twilio WhatsApp API.
    numero_destino debe tener el formato: whatsapp:+584121234567
    """
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    payload = {
        "From": TWILIO_WHATSAPP_FROM,
        "To":   numero_destino,
        "Body": mensaje
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            data=payload,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        )

    if response.status_code == 201:
        print(f"[TWILIO OK] Mensaje enviado a {numero_destino}")
    else:
        print(f"[TWILIO ERROR] {response.status_code} — {response.text}")

    return response


# ── Ruta raíz: verificar que el servidor está vivo ───────────────────
@app.get("/")
def home():
    """Ruta de verificación. Confirma que el servidor está activo."""
    return {
        "status": "AGUIBot operativo",
        "version": "2.1.0",
        "mensaje": "Servidor FastAPI corriendo correctamente"
    }


# ── Ruta principal: Webhook de Twilio WhatsApp ───────────────────────
#
# FASE 4 — CONTROL DE ERRORES HTTP
# ---------------------------------------------------------------------
# Antes, `From` y `Body` se declaraban como Form(...) obligatorios.
# Eso significa que si Twilio (o cualquier mensaje "raro": una imagen,
# un sticker, un webhook mal formado, un campo faltante) llegaba sin
# esos campos exactos, FastAPI respondía un 422 automáticamente ANTES
# de que nuestro código llegara a ejecutarse — el try/except nunca se
# alcanzaba, y Twilio interpretaba el error como fallo de entrega y
# reintentaba el mismo mensaje una y otra vez.
#
# Ahora se lee el formulario manualmente con request.form(), con valores
# por defecto seguros, y TODO el cuerpo de la función está envuelto en
# un try/except general. Pase lo que pase — payload corrupto, campo
# faltante, error de red al hablar con Twilio — siempre se responde
# 200 OK (para que Twilio no siga reintentando) y, si se pudo identificar
# al usuario, se le manda un mensaje de error amigable.
@app.post("/webhook")
async def recibir_mensaje(request: Request):
    """
    Recibe los mensajes entrantes de WhatsApp via Twilio.

    Twilio envía un formulario con:
    - From: número del cliente (ej. whatsapp:+584121234567)
    - Body: texto del mensaje que escribió el cliente

    Blindado para que un mensaje malformado o inesperado nunca tumbe
    el servidor ni provoque reintentos infinitos de Twilio.
    """
    user_id = None

    try:
        # ── Paso 1: Extraer y limpiar los datos de forma segura ─────
        form = await request.form()
        user_id    = str(form.get("From", "") or "").strip()
        user_input = str(form.get("Body", "") or "").strip()

        if not user_id:
            # No hay a quién responder: se registra y se corta aquí,
            # pero igual devolvemos 200 más abajo.
            print("[WEBHOOK] Payload sin remitente (From). Se ignora.")
            return PlainTextResponse("OK", status_code=200)

        print(f"[WEBHOOK] Mensaje recibido de {user_id}: '{user_input}'")

        # ── Paso 2: Pasar a la máquina de estados (cerebro de Ángel) ─
        try:
            respuesta_bot = maquina.procesar_transicion(user_id, user_input)
        except Exception as e:
            print(f"[ERROR FSM] {e}")
            respuesta_bot = MENSAJE_ERROR_USUARIO

        print(f"[WEBHOOK] Respuesta del bot: '{respuesta_bot}'")

        # ── Paso 3: Enviar respuesta de vuelta a WhatsApp ────────────
        await enviar_mensaje_whatsapp(
            numero_destino=user_id,
            mensaje=respuesta_bot
        )

    except Exception as e:
        # Red de seguridad final: cualquier fallo no previsto (form
        # malformado, timeout de Twilio, lo que sea) cae aquí. Se
        # intenta avisarle al usuario si se llegó a identificar su
        # número; si ni eso se pudo, simplemente se registra el error.
        print(f"[ERROR WEBHOOK] {e}")
        if user_id:
            try:
                await enviar_mensaje_whatsapp(
                    numero_destino=user_id,
                    mensaje=MENSAJE_ERROR_USUARIO
                )
            except Exception as e2:
                print(f"[ERROR ENVÍO FALLBACK] {e2}")

    # ── Paso 4: Confirmar a Twilio que el webhook fue procesado ──────
    # SIEMPRE 200 OK, incluso ante errores — así Twilio nunca reintenta
    # el mismo mensaje pensando que el servidor está caído.
    return PlainTextResponse("OK", status_code=200)


# ── Ruta de prueba: simular un mensaje sin WhatsApp real ─────────────
@app.post("/test")
async def test_mensaje(user_id: str, mensaje: str):
    """
    Ruta de prueba local. Permite probar la máquina de estados
    sin necesitar WhatsApp ni Twilio.

    Uso: POST /test?user_id=usuario_prueba&mensaje=hola
    """
    try:
        respuesta = maquina.procesar_transicion(user_id, mensaje)
    except Exception as e:
        respuesta = f"Error: {str(e)}"

    return {
        "user_id":   user_id,
        "entrada":   mensaje,
        "respuesta": respuesta
    }
