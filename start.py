# start.py
# Entry point for AGUI ChatBot.
# The health check runs automatically inside FastAPI's startup event (main.py).
import sys
import subprocess


def iniciar_proyecto():
    print("🚀 Iniciando AGUIBot (FastAPI + health check integrado)...")
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload"])


if __name__ == "__main__":
    iniciar_proyecto()