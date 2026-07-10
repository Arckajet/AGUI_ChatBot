# CÓDIGO DE ELIAS (Lectura y escritura de inventario.json)
import json
import os

# 1. Función general para leer cualquier archivo JSON de inventario
def leer_inventario(archivo_ruta):
    """Lee el archivo JSON y devuelve los datos como un diccionario de Python."""
    if not os.path.exists(archivo_ruta):
        return {"productos": []} # Devuelve estructura vacía si el archivo no existe
        
    with open(archivo_ruta, 'r', encoding='utf-8') as archivo:
        return json.load(archivo)

# 2. Función general para guardar/actualizar el archivo JSON
def guardar_inventario(archivo_ruta, datos):
    """Guarda el diccionario actualizado en el archivo JSON."""
    # Asegura que si la carpeta contenedora (como 'data') no existe, la cree automáticamente
    carpeta = os.path.dirname(archivo_ruta)
    if carpeta and not os.path.exists(carpeta):
        os.makedirs(carpeta)
        
    with open(archivo_ruta, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

# 3. FUNCIÓN CRÍTICA: Validar si hay stock disponible
def verificar_stock(archivo_ruta, producto_id, cantidad_solicitada=1):
    """
    Busca un producto por su ID y verifica si tiene suficiente stock.
    Retorna True si hay stock, False si no hay o si el producto no existe.
    """
    inventario = leer_inventario(archivo_ruta)
    
    for producto in inventario.get("productos", []):
        if producto["id"] == producto_id:
            if producto["stock"] >= cantidad_solicitada:
                return True
            else:
                print(f"Stock insuficiente para {producto['nombre']}. Disponibles: {producto['stock']}")
                return False
                
    print("Producto no encontrado.")
    return False

# 4. Función para actualizar el stock (restar cuando compren)
def actualizar_stock(archivo_ruta, producto_id, cantidad_comprada):
    """Resta la cantidad comprada del stock del producto."""
    inventario = leer_inventario(archivo_ruta)
    
    for producto in inventario.get("productos", []):
        if producto["id"] == producto_id:
            if producto["stock"] >= cantidad_comprada:
                producto["stock"] -= cantidad_comprada
                guardar_inventario(archivo_ruta, inventario)
                return True
    return False