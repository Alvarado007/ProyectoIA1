from modelos import Salon, Franja, Profesor, Curso


# Carga los salones desde el archivo de texto
def cargar_salones(ruta):
    salones = []
    with open(ruta, mode='r', encoding='utf-8') as archivo:
        for linea in archivo:
            nombre = linea.strip()
            # ignorar lineas vacias o comentarios
            if nombre and not nombre.startswith('#'):
                salones.append(Salon(nombre))
    return salones


# Carga las franjas horarias con formato Dia,Hora
def cargar_franjas(ruta):
    franjas = []
    with open(ruta, mode='r', encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                partes = linea.split(',')
                if len(partes) >= 2:
                    dia = partes[0].strip()
                    hora = partes[1].strip()
                    franjas.append(Franja(dia, hora))
    return franjas


# Carga los profesores y sus franjas no disponibles
def cargar_profesores(ruta):
    profesores = []
    with open(ruta, mode='r', encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                partes = linea.split(',', 1)
                nombre = partes[0].strip()
                no_disponibles = []
                
                # revisar si tiene franjas restringidas
                if len(partes) > 1:
                    franjas_str = partes[1].strip()
                    if franjas_str and franjas_str.lower() != 'ninguna':
                        items = franjas_str.split('|')
                        for item in items:
                            item = item.strip()
                            if not item:
                                continue
                            if '_' in item:
                                dia, hora = item.split('_', 1)
                            elif ',' in item:
                                dia, hora = item.split(',', 1)
                            else:
                                dia, hora = item, ""
                            no_disponibles.append(Franja(dia.strip(), hora.strip()))
                
                profesores.append(Profesor(nombre, no_disponibles))
    return profesores


# Carga los cursos (materia, profesor, grupo)
def cargar_cursos(ruta):
    cursos = []
    with open(ruta, mode='r', encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                partes = linea.split(',')
                if len(partes) >= 3:
                    materia = partes[0].strip()
                    profesor = partes[1].strip()
                    grupo = partes[2].strip()
                    cursos.append(Curso(materia, profesor, grupo))
    return cursos


if __name__ == "__main__":
    import os
    
    # prueba rapida del cargador
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    carpeta_datos = os.path.join(directorio_actual, "datos")
    
    print("Probando cargador...")
    salones = cargar_salones(os.path.join(carpeta_datos, "salones.txt"))
    franjas = cargar_franjas(os.path.join(carpeta_datos, "franjas.txt"))
    profesores = cargar_profesores(os.path.join(carpeta_datos, "profesores.txt"))
    cursos = cargar_cursos(os.path.join(carpeta_datos, "cursos.txt"))
    
    print(f"Salones: {len(salones)}")
    print(f"Franjas: {len(franjas)}")
    print(f"Profesores: {len(profesores)}")
    print(f"Cursos: {len(cursos)}")
