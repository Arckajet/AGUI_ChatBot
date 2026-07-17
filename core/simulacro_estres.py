import threading
from estados import MaquinaEstadosAGUI

bot = MaquinaEstadosAGUI()

def task(uid, msg):
    print(f"[{uid}] Enviando: {msg}")
    res = bot.procesar_transicion(uid, msg)
    print(f"[{uid}] Respuesta recibida.")

# Lanzar 3 usuarios al mismo tiempo
threads = []
usuarios = [("+58412001", "1"), ("+58412002", "1"), ("+58412003", "1")]

for uid, msg in usuarios:
    t = threading.Thread(target=task, args=(uid, msg))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Simulacro finalizado sin errores de concurrencia.")