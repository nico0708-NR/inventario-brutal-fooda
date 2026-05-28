inventario = []

archivo = "datos.txt"


def cargar_inventario():

    try:

        with open(archivo, "r") as file:

            for linea in file:

                datos = linea.strip().split(",")

                if len(datos) == 2:
                    inventario.append(datos)

    except FileNotFoundError:
        pass


def guardar_inventario():

    with open(archivo, "w") as file:

        for producto in inventario:

            file.write(f"{producto[0]},{producto[1]}\n")