# Servidor central de FastAPI

# pyrefly: ignore [missing-import]
from fastapi import FastAPI

app = FastAPI(
    title="AGUIBot API",
    description="Backend para el asistente de gestión de usuarios e interfaces",
    version="1.0.0"
)

@app.get("/")
def home():
    return {"status": "AGUIBot operativo", "version": "1.0.0"}

# Aquí llegará el Webhook de WhatsApp más adelante
@app.post("/webhook")
def recibir_mensaje(payload: dict):
    # Aquí se conectará la máquina de estados de Ángel
    print("Mensaje recibido:", payload)
    return {"status": "procesado"}