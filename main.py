# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - SERVIDOR FASTAPI (WEBHOOK)
# DESARROLLADOR: WILLIAM RODRIGUEZ
# FASE 3 - ARQUITECTO DEL SERVIDOR
# =====================================================================

from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
import httpx
import os

# Importar el cerebro del bot (Ángel)
from estados import MaquinaEstadosAGUI

# ── Inicializar la app y la máquina de estados ──────────────────────
app = FastAPI(
    title="AGUIBot API",
    description="Backend del asistente de autoatención AGUI",
    version="2.0.0"
)

# Una sola instancia de la máquina compartida por todos los usuarios
maquina = MaquinaEstadosAGUI()

# ── Credenciales Twilio (se leen desde variables de entorno) ─────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


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
        "version": "2.0.0",
        "mensaje": "Servidor FastAPI corriendo correctamente"
    }


# ── Ruta principal: Webhook de Twilio WhatsApp ───────────────────────
@app.post("/webhook")
async def recibir_mensaje(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...)
):
    """
    Recibe los mensajes entrantes de WhatsApp via Twilio.

    Twilio envía un formulario con:
    - From: número del cliente (ej. whatsapp:+584121234567)
    - Body: texto del mensaje que escribió el cliente

    Flujo:
    1. Extraer user_id y mensaje del formulario
    2. Pasarlo a la MaquinaEstadosAGUI
    3. Obtener la respuesta formateada
    4. Enviarla de vuelta al cliente por WhatsApp
    """

    # ── Paso 1: Extraer y limpiar los datos ─────────────────────────
    user_id      = From.strip()        # ej: "whatsapp:+584121234567"
    user_input   = Body.strip()        # ej: "1" o "hola" o "menu"

    print(f"[WEBHOOK] Mensaje recibido de {user_id}: '{user_input}'")

    # ── Paso 2: Pasar a la máquina de estados (cerebro de Ángel) ────
    try:
        respuesta_bot = maquina.procesar_transicion(user_id, user_input)
    except Exception as e:
        print(f"[ERROR FSM] {e}")
        respuesta_bot = (
            "Ocurrio un error interno. Por favor escribe *Menu* para reiniciar."
        )

    print(f"[WEBHOOK] Respuesta del bot: '{respuesta_bot}'")

    # ── Paso 3: Enviar respuesta de vuelta a WhatsApp ────────────────
    await enviar_mensaje_whatsapp(
        numero_destino=user_id,
        mensaje=respuesta_bot
    )

    # ── Paso 4: Confirmar a Twilio que el webhook fue procesado ──────
    # Twilio espera un 200 OK. Si no lo recibe, reintenta el envío.
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
