# INVENTARIO BRUTAL FOOD - CONSOLA

inventario = []

def agregar_producto():
    nombre = input("Nombre del producto: ")
    cantidad = int(input("Cantidad: "))

    inventario.append({
        "nombre": nombre,
        "cantidad": cantidad
    })

    print("✔ Producto agregado correctamente")


def mostrar_inventario():
    print("\n📦 INVENTARIO ACTUAL\n")

    if len(inventario) == 0:
        print("No hay productos registrados.")
        return

    for i, producto in enumerate(inventario, start=1):
        print(f"{i}. {producto['nombre']} - {producto['cantidad']} unidades")


def buscar_producto():
    nombre = input("Nombre del producto a buscar: ")

    encontrado = False

    for producto in inventario:
        if producto["nombre"].lower() == nombre.lower():
            print(f"✔ Encontrado: {producto['nombre']} - {producto['cantidad']} unidades")
            encontrado = True

    if not encontrado:
        print("❌ Producto no encontrado")


def editar_producto():
    nombre = input("Producto a editar: ")

    for producto in inventario:
        if producto["nombre"].lower() == nombre.lower():
            nueva_cantidad = int(input("Nueva cantidad: "))
            producto["cantidad"] = nueva_cantidad
            print("✔ Producto actualizado")
            return

    print("❌ Producto no encontrado")


def eliminar_producto():
    nombre = input("Producto a eliminar: ")

    for producto in inventario:
        if producto["nombre"].lower() == nombre.lower():
            inventario.remove(producto)
            print("✔ Producto eliminado")
            return

    print("❌ Producto no encontrado")


def estadisticas():
    total = 0

    for producto in inventario:
        total += producto["cantidad"]

    print("\n📊 ESTADÍSTICAS")
    print(f"Total de productos registrados: {len(inventario)}")
    print(f"Total de unidades en inventario: {total}")


while True:
    print("\n===== INVENTARIO BRUTAL FOOD =====")
    print("1. Agregar producto")
    print("2. Mostrar inventario")
    print("3. Buscar producto")
    print("4. Editar producto")
    print("5. Eliminar producto")
    print("6. Ver estadísticas")
    print("7. Salir")

    opcion = input("Elige una opción: ")

    if opcion == "1":
        agregar_producto()

    elif opcion == "2":
        mostrar_inventario()

    elif opcion == "3":
        buscar_producto()

    elif opcion == "4":
        editar_producto()

    elif opcion == "5":
        eliminar_producto()

    elif opcion == "6":
        estadisticas()

    elif opcion == "7":
        print("Saliendo del sistema...")
        break

    else:
        print("❌ Opción inválida")