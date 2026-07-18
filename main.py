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
import time
import interfaz
from utils.check_system import main as run_check
from utils.ux_helper import UXHelper


def safe_print(*args, **kwargs):
    """Imprime de forma segura en la consola de Windows evitando UnicodeEncodeError."""
    try:
        text = " ".join(str(arg) for arg in args)
        print(text, **kwargs)
    except UnicodeEncodeError:
        try:
            # Reemplazar emojis/caracteres no cp1252 con "?"
            clean_text = text.encode('ascii', errors='replace').decode('ascii')
            print(clean_text, **kwargs)
        except Exception:
            pass

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

# Una sola instancia de la máquina compartida por todos los usuarios
maquina = MaquinaEstadosAGUI()

# Mensaje de error genérico pedido en la guía de Fase 4
MENSAJE_ERROR_USUARIO = "⚠️ Error, intenta de nuevo. Escribe *Menu* para reiniciar."


# ── Función auxiliar: enviar mensaje de vuelta a WhatsApp con la nueva API ────────────
async def enviar_mensaje(numero_destino: str, mensaje: str) -> bool:
    """
    Envía un mensaje de texto al cliente a través del nuevo proveedor WASender.
    """
    url = os.getenv("WASENDER_API_URL", "https://api.wasenderapi.com/v1/send/message")
    token = os.getenv("WASENDER_API_TOKEN", "")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": numero_destino,
        "text": mensaje
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=10.0
            )

        if response.status_code in [200, 201]:
            print(f"[WASENDER OK] Mensaje enviado a {numero_destino}")
            return True
        else:
            print(f"[WASENDER ERROR] {response.status_code} — {response.text}")
            return False

    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
        print(f"[WASENDER EXCEPTION] Error al conectar con WASender para {numero_destino}: {e}")
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
    Recibe los mensajes entrantes de WhatsApp via WASender API.
    Extrae sender y message del JSON.
    """
    user_id = None

    try:
        # ── Paso 1: Extraer y limpiar los datos de forma segura desde JSON ─────
        try:
            data = await request.json()
        except Exception:
            data = {}

        safe_print(f"[WEBHOOK DEBUG] Payload recibido: {data}")

        # Estructura de WASender: data -> messages -> key/messageBody
        inner_data = data.get("data", {})
        messages = inner_data.get("messages", {})
        key = messages.get("key", {})

        # Ignorar mensajes enviados por el propio bot para evitar bucles de respuesta
        if key.get("fromMe") is True:
            safe_print("[WEBHOOK] Mensaje enviado por el propio bot (fromMe=True). Se ignora.")
            return {"status": "ok"}

        # Extraemos el remitente (priorizando cleanedSenderPn de key)
        user_id = str(key.get("cleanedSenderPn") or "").strip()
        if not user_id:
            sender_pn = str(key.get("senderPn") or "").strip()
            if "@" in sender_pn:
                user_id = sender_pn.split("@")[0]
            else:
                user_id = sender_pn

        # Extraemos el mensaje (messageBody o conversation)
        user_input = str(messages.get("messageBody") or messages.get("message", {}).get("conversation") or "").strip()

        if not user_id:
            # No hay a quién responder: se registra y se corta aquí.
            safe_print("[WEBHOOK] Payload sin remitente (cleanedSenderPn). Se ignora.")
            return {"status": "ok"}

        safe_print(f"[WEBHOOK] Mensaje recibido de {user_id}: '{user_input}'")

        # ── Paso 2: Pasar a la máquina de estados (cerebro de Ángel) ─
        try:
            # --- Carga de estado previo (Fase 3) ---
            sesiones_guardadas = cargar_sesiones()
            ahora = time.time()
            es_primera_vez_o_expirado = False

            if user_id in sesiones_guardadas:
                sesion_usuario = sesiones_guardadas[user_id]
                last_interaction = sesion_usuario.get("last_interaction", 0)
                
                # Expiración tras 24 horas (86400 segundos) de inactividad
                if ahora - last_interaction > 86400:
                    es_primera_vez_o_expirado = True
                
                maquina.sesiones[user_id] = sesion_usuario
            else:
                es_primera_vez_o_expirado = True
                maquina.sesiones[user_id] = {
                    "estado": maquina.ESTADO_MENU_PRINCIPAL,
                    "tienda_actual": maquina.DB_PASTELERIA
                }

            if es_primera_vez_o_expirado:
                # Forzar reset y enviar bienvenida en la primera interacción o tras 24h
                maquina.sesiones[user_id]["estado"] = maquina.ESTADO_MENU_PRINCIPAL
                maquina.sesiones[user_id]["tienda_actual"] = maquina.DB_PASTELERIA
                respuesta_bot = interfaz.mostrar_bienvenida()
            else:
                if user_input.lower() in ["/ayuda", "ayuda"]:
                    respuesta_bot = UXHelper.get_user_manual()
                else:
                    respuesta_bot = maquina.procesar_transicion(user_id, user_input)
                
            # --- Guardado de estado (Fase 3) ---
            maquina.sesiones[user_id]["last_interaction"] = ahora
            sesiones_guardadas[user_id] = maquina.sesiones[user_id]
            guardar_sesiones(sesiones_guardadas)

        except Exception as e:
            safe_print(f"[ERROR FSM] {e}")
            respuesta_bot = UXHelper.format_error("Hubo un problema interno procesando tu solicitud.")

        safe_print(f"[WEBHOOK] Respuesta lógica generada (longitud: {len(respuesta_bot)})")

        # ── Paso 3: Enviar respuesta de vuelta a WhatsApp ────────────
        enviado = await enviar_mensaje(
            numero_destino=user_id,
            mensaje=respuesta_bot
        )
        
        if enviado:
            safe_print(f"[WEBHOOK] Enviado con éxito a {user_id}")
        else:
            safe_print(f"[WEBHOOK ERROR] No se pudo entregar el mensaje a {user_id}")

    except Exception as e:
        # Red de seguridad final: cualquier fallo no previsto cae aquí.
        safe_print(f"[ERROR WEBHOOK] {e}")
        if user_id:
            try:
                enviado_fallback = await enviar_mensaje(
                    numero_destino=user_id,
                    mensaje=UXHelper.format_error("Hubo un problema procesando tu solicitud. Escribe *Menu* para reiniciar.")
                )
                if enviado_fallback:
                    safe_print(f"[WEBHOOK] Mensaje de fallback (error) enviado a {user_id}")
                else:
                    safe_print(f"[WEBHOOK ERROR] Falló el envío del fallback a {user_id}")
            except Exception as e2:
                safe_print(f"[ERROR ENVÍO FALLBACK] {e2}")

    # Retornamos respuesta simple para confirmar la recepción
    return {"status": "ok"}


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
        respuesta = UXHelper.format_error(str(e))

    return {
        "user_id":   user_id,
        "entrada":   mensaje,
        "respuesta": respuesta
    }
