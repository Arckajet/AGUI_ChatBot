# =====================================================================
# UNIVERSIDAD BICENTENARIA DE ARAGUA
# FACULTAD DE INGENIERÍA - SISTEMAS DE INFORMACIÓN
# PROYECTO: AGUIBOT - SERVIDOR FASTAPI (WEBHOOK)
# DESARROLLADOR: WILLIAM RODRIGUEZ
# FASE 4 - ESTABILIZACIÓN DEL BACKEND (CONCURRENCIA Y ERRORES HTTP)
# =====================================================================

# Importaciones
# pyrefly: ignore [missing-import]
import uvicorn
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, Response
# pyrefly: ignore [missing-import]
from fastapi.responses import PlainTextResponse
# pyrefly: ignore [missing-import]
import httpx
# pyrefly: ignore [missing-import]
import os
import json
from utils.check_system import main as run_check
from utils.ux_helper import UXHelper

from twilio.rest import Client

RUTA_SESIONES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sesiones_usuarios.json")

def cargar_sesiones():
    """Carga las sesiones desde el archivo JSON de forma segura."""
    try:
        with open(RUTA_SESIONES, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si no existe o está corrupto, retorna un dict vacío y no tumba el server
        return {}

def guardar_sesiones(sesiones_dict):
    """Guarda las sesiones en el archivo JSON."""
    try:
        os.makedirs(os.path.dirname(RUTA_SESIONES), exist_ok=True)
        with open(RUTA_SESIONES, "w", encoding="utf-8") as f:
            json.dump(sesiones_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERROR PERSISTENCIA] No se pudo guardar la sesión: {e}")

# Importar el cerebro del bot (Ángel)
from core.estados import MaquinaEstadosAGUI

# ── Inicializar la app y la máquina de estados ──────────────────────
app = FastAPI(
    title="AGUIBot API",
    description="Backend del asistente de autoatención AGUI",
    version="2.1.0"
)

# --- EJECUCIÓN DEL CHEQUEO AL INICIO ---
print("🚀 Verificando sistema antes de arrancar...")
run_check()

# Una sola instancia de la máquina compartida por todos los usuarios
maquina = MaquinaEstadosAGUI()

# Mensaje de error genérico pedido en la guía de Fase 4
MENSAJE_ERROR_USUARIO = "⚠️ Error, intenta de nuevo. Escribe *Menu* para reiniciar."


# ── Función auxiliar: enviar mensaje de vuelta a WhatsApp ────────────
async def enviar_mensaje_whatsapp(numero_destino: str, mensaje: str) -> bool:
    """
    Envía un mensaje de texto al cliente via Twilio WhatsApp API.
    numero_destino debe tener el formato: whatsapp:+584121234567.
    Si no tiene el prefijo 'whatsapp:', se le añade automáticamente.
    """
    # Cargar credenciales localmente para evitar variables globales
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Validación y formateo del número de destino
    if not numero_destino.startswith("whatsapp:"):
        numero_destino = f"whatsapp:{numero_destino}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    payload = {
        "From": whatsapp_from,
        "To":   numero_destino,
        "Body": mensaje
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=payload,
                auth=(account_sid, auth_token),
                timeout=10.0
            )

        if response.status_code == 201:
            print(f"[TWILIO OK] Mensaje enviado a {numero_destino}")
            return True
        else:
            print(f"[TWILIO ERROR] {response.status_code} — {response.text}")
            return False

    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
        print(f"[TWILIO EXCEPTION] Error al conectar con Twilio para {numero_destino}: {e}")
        return False


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
            # --- Carga de estado previo (Fase 3) ---
            sesiones_guardadas = cargar_sesiones()
            if user_id in sesiones_guardadas:
                maquina.sesiones[user_id] = sesiones_guardadas[user_id]
            else:
                maquina.sesiones[user_id] = {
                    "estado": maquina.ESTADO_MENU_PRINCIPAL,
                    "tienda_actual": maquina.DB_PASTELERIA
                }

            if user_input.lower() in ["/ayuda", "ayuda"]:
                respuesta_bot = UXHelper.get_user_manual()
            else:
                respuesta_bot = maquina.procesar_transicion(user_id, user_input)
                
            # --- Guardado de estado (Fase 3) ---
            sesiones_guardadas[user_id] = maquina.sesiones[user_id]
            guardar_sesiones(sesiones_guardadas)

        except Exception as e:
            print(f"[ERROR FSM] {e}")
            respuesta_bot = UXHelper.format_error("Hubo un problema interno procesando tu solicitud.")

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
