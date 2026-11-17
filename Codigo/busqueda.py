import time
from modelos import Salon, Franja, Profesor, Curso, Asignacion, Nodo


# Guarda las metricas del algoritmo para la interfaz
class ResultadoBusqueda:
    def __init__(self, nodo_solucion, nodos_explorados, tiempo_segundos, encontro_solucion):
        self.nodo_solucion = nodo_solucion
        self.nodos_explorados = nodos_explorados
        self.tiempo_segundos = tiempo_segundos
        self.encontro_solucion = encontro_solucion

    def __iter__(self):
        return iter((self.nodo_solucion, self.nodos_explorados, self.tiempo_segundos, self.encontro_solucion))


# Clase principal del problema de horarios (CSP)
class ProblemaHorario:
    def __init__(self, cursos, profesores, salones, franjas, max_consecutivas=2):
        self.cursos = cursos
        self.profesores = profesores
        self.salones = salones
        self.franjas = franjas
        self.max_consecutivas = max_consecutivas

        # Diccionario para buscar al profesor en O(1)
        self.profesores_dict = {p.nombre: p for p in self.profesores}

        # Dominio: combinaciones de (franja, salon)
        self.dominio = []
        for franja in self.franjas:
            for salon in self.salones:
                self.dominio.append((franja, salon))

    # Verifica si ya se asignaron todos los cursos
    def es_meta(self, nodo):
        return nodo.nivel == len(self.cursos)

    # Revisa restricciones duras: mismo salon, mismo profesor o mismo grupo a la misma hora
    def es_valida(self, asignaciones, nueva_asig):
        for asig in asignaciones:
            # solo hay conflicto si coinciden en la misma franja
            if asig.franja == nueva_asig.franja:
                if asig.salon.nombre == nueva_asig.salon.nombre:
                    return False
                if asig.curso.nombre_profesor == nueva_asig.curso.nombre_profesor:
                    return False
                if asig.curso.grupo == nueva_asig.curso.grupo:
                    return False
        return True

    # Costo base 1 mas penalizaciones de restricciones blandas (+5)
    def calcular_costo(self, asignaciones, nueva_asig):
        costo = 1

        # penalizacion si la franja no le gusta al profesor
        profesor = self.profesores_dict.get(nueva_asig.curso.nombre_profesor)
        if profesor:
            if nueva_asig.franja in profesor.franjas_no_disponibles:
                costo += 5

        # penalizacion si el grupo supera el maximo de clases en el mismo dia
        clases_dia = sum(
            1 for asig in asignaciones
            if asig.curso.grupo == nueva_asig.curso.grupo
            and asig.franja.dia == nueva_asig.franja.dia
        )
        if (clases_dia + 1) > self.max_consecutivas:
            costo += 5

        return costo

    # Heuristica: materias que faltan por asignar
    def calcular_h(self, asignaciones, nivel_hijo):
        faltantes = len(self.cursos) - nivel_hijo
        return max(0, faltantes)

    # Genera los hijos validos asignando el siguiente curso
    def obtener_sucesores(self, nodo):
        if nodo.nivel >= len(self.cursos):
            return []

        curso_actual = self.cursos[nodo.nivel]
        sucesores = []

        for franja, salon in self.dominio:
            nueva_asig = Asignacion(curso_actual, franja, salon)

            # poda por restricciones duras
            if self.es_valida(nodo.asignaciones, nueva_asig):
                costo = self.calcular_costo(nodo.asignaciones, nueva_asig)
                h = self.calcular_h(nodo.asignaciones, nodo.nivel + 1)

                hijo = nodo.crear_hijo(
                    nueva_asignacion=nueva_asig,
                    costo_paso=costo,
                    nueva_h=h
                )
                sucesores.append(hijo)

        return sucesores


# Algoritmo BFS usando cola FIFO
def busqueda_amplitud(problema):
    inicio = time.perf_counter()
    frontera = [Nodo()]
    nodos_explorados = 0

    while frontera:
        nodo = frontera.pop(0)  # FIFO
        nodos_explorados += 1

        if problema.es_meta(nodo):
            tiempo = time.perf_counter() - inicio
            return ResultadoBusqueda(nodo, nodos_explorados, tiempo, True)

        sucesores = problema.obtener_sucesores(nodo)
        frontera.extend(sucesores)

    tiempo = time.perf_counter() - inicio
    return ResultadoBusqueda(None, nodos_explorados, tiempo, False)


# DFS auxiliar con limite de profundidad
def dfs_limitado(problema, nodo_raiz, limite):
    frontera = [nodo_raiz]
    nodos_explorados = 0

    while frontera:
        nodo = frontera.pop()  # LIFO (pila)
        nodos_explorados += 1

        if problema.es_meta(nodo):
            return (nodo, nodos_explorados, True)

        if nodo.nivel < limite:
            sucesores = problema.obtener_sucesores(nodo)
            frontera.extend(reversed(sucesores))

    return (None, nodos_explorados, False)


# Algoritmo IDDFS aumentando el limite de profundidad
def busqueda_profundidad_iterativa(problema):
    inicio = time.perf_counter()
    total_explorados = 0
    limite_max = len(problema.cursos)

    for limite in range(limite_max + 1):
        nodo_raiz = Nodo()
        solucion, nodos_paso, encontro = dfs_limitado(problema, nodo_raiz, limite)
        total_explorados += nodos_paso

        if encontro:
            tiempo = time.perf_counter() - inicio
            return ResultadoBusqueda(solucion, total_explorados, tiempo, True)

    tiempo = time.perf_counter() - inicio
    return ResultadoBusqueda(None, total_explorados, tiempo, False)


# Algoritmo UCS ordenando por menor costo acumulado g
def busqueda_costo_uniforme(problema):
    inicio = time.perf_counter()
    frontera = [Nodo()]
    nodos_explorados = 0

    while frontera:
        # ordenar por menor costo g(n)
        frontera.sort(key=lambda n: n.costo_g)
        nodo = frontera.pop(0)
        nodos_explorados += 1

        if problema.es_meta(nodo):
            tiempo = time.perf_counter() - inicio
            return ResultadoBusqueda(nodo, nodos_explorados, tiempo, True)

        sucesores = problema.obtener_sucesores(nodo)
        frontera.extend(sucesores)

    tiempo = time.perf_counter() - inicio
    return ResultadoBusqueda(None, nodos_explorados, tiempo, False)


# Algoritmo A* (A-Prima) ordenando por f = g + h
def busqueda_a_prima(problema):
    inicio = time.perf_counter()
    h_inicial = len(problema.cursos)
    raiz = Nodo(heuristica_h=h_inicial)
    frontera = [raiz]
    nodos_explorados = 0

    while frontera:
        # ordenar por menor f(n) y desempatar por mayor nivel
        frontera.sort(key=lambda n: (n.costo_f, -n.nivel))
        nodo = frontera.pop(0)
        nodos_explorados += 1

        if problema.es_meta(nodo):
            tiempo = time.perf_counter() - inicio
            return ResultadoBusqueda(nodo, nodos_explorados, tiempo, True)

        sucesores = problema.obtener_sucesores(nodo)
        frontera.extend(sucesores)

    tiempo = time.perf_counter() - inicio
    return ResultadoBusqueda(None, nodos_explorados, tiempo, False)


if __name__ == "__main__":
    from cargador import cargar_salones, cargar_franjas, cargar_profesores, cargar_cursos
    import os

    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    carpeta_datos = os.path.join(directorio_actual, "datos")

    salones = cargar_salones(os.path.join(carpeta_datos, "salones.txt"))
    franjas = cargar_franjas(os.path.join(carpeta_datos, "franjas.txt"))
    profesores = cargar_profesores(os.path.join(carpeta_datos, "profesores.txt"))
    cursos = cargar_cursos(os.path.join(carpeta_datos, "cursos.txt"))

    problema = ProblemaHorario(cursos, profesores, salones, franjas, max_consecutivas=2)

    print("=== Asignacion de Horarios ===")
    print(f"Cursos: {len(cursos)}, Salones: {len(salones)}, Franjas: {len(franjas)}, Profesores: {len(profesores)}")

    algoritmos = [
        ("BFS", busqueda_amplitud),
        ("IDDFS", busqueda_profundidad_iterativa),
        ("UCS", busqueda_costo_uniforme),
        ("A*", busqueda_a_prima),
    ]

    for nombre, funcion in algoritmos:
        res = funcion(problema)
        costo = res.nodo_solucion.costo_g if res.encontro_solucion else "N/A"
        print(f"{nombre:<6} | Nodos: {res.nodos_explorados:<4} | Tiempo: {res.tiempo_segundos:.6f}s | Costo: {costo}")
