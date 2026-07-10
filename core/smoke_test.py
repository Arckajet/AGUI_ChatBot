"""Quick smoke test for hardened MaquinaEstadosAGUI."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from estados import MaquinaEstadosAGUI

bot = MaquinaEstadosAGUI()
uid1 = "+584121234567"
uid2 = "+584129999999"
passed = 0
total = 0

def test(name, result, expected_substring):
    global passed, total
    total += 1
    ok = expected_substring in result
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    print(f"[{status}] {name}")
    if not ok:
        print(f"  Expected substring: {expected_substring!r}")
        print(f"  Got: {result[:120]!r}...")

# 1. Normal welcome
test("Bienvenida via hola",
     bot.procesar_transicion(uid1, "hola"),
     "AGUI Chatbot")

# 2. None input
test("Rechaza None",
     bot.procesar_transicion(uid1, None),
     "Solo acepto comandos de texto")

# 3. Empty string
test("Rechaza string vacio",
     bot.procesar_transicion(uid1, "   "),
     "No recib")

# 4. Dict input (simulates image payload)
test("Rechaza dict (imagen)",
     bot.procesar_transicion(uid1, {"type": "image", "url": "https://..."}),
     "Solo acepto comandos de texto")

# 5. Navigate to catalog
resp5 = bot.procesar_transicion(uid1, "1")
test("Navega a Pasteleria",
     resp5,
     "PAST")

# 6. Global escape from catalog
assert bot.sesiones[uid1]["estado"] == "VISTA_CATALOGO"
resp6 = bot.procesar_transicion(uid1, "menu")
test("Global escape desde catalogo",
     resp6,
     "AGUI Chatbot")
assert bot.sesiones[uid1]["estado"] == "MENU_PRINCIPAL"

# 7. Fallback in main menu
test("Fallback contextual en menu",
     bot.procesar_transicion(uid1, "xyz"),
     "1 al 4")

# 8. Multi-user isolation
bot.procesar_transicion(uid1, "1")  # uid1 -> Pasteleria
bot.procesar_transicion(uid2, "2")  # uid2 -> Videojuegos
s1 = bot.sesiones[uid1]
s2 = bot.sesiones[uid2]
isolated = (
    s1["estado"] == "VISTA_CATALOGO"
    and s2["estado"] == "VISTA_CATALOGO"
    and "pasteleria" in s1["tienda_actual"].lower()
    and "videojuegos" in s2["tienda_actual"].lower()
)
total += 1
if isolated:
    passed += 1
    print("[PASS] Multi-user isolation")
else:
    print("[FAIL] Multi-user isolation")
    print(f"  uid1: {s1}")
    print(f"  uid2: {s2}")

# 9. Accented command
bot.procesar_transicion(uid1, "hola")  # reset
bot.procesar_transicion(uid1, "4")     # go to soporte
assert bot.sesiones[uid1]["estado"] == "MENU_SOPORTE"
resp9 = bot.procesar_transicion(uid1, "men\u00fa")  # menú with accent
test("Comando global con acento (menu)",
     resp9,
     "AGUI Chatbot")

# 10. Control chars only
test("Rechaza solo control chars",
     bot.procesar_transicion(uid1, "\x00\x01\x02"),
     "Solo acepto comandos de texto")

print(f"\n{'='*40}")
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
