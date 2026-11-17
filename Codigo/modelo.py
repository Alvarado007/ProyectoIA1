class Salon:
    def __init__(self, nombre):
        self.nombre = nombre.strip()

    def __repr__(self):
        return f"Salon({self.nombre})"


class Franja:
    def __init__(self, dia, hora):
        self.dia = dia.strip()
        self.hora = hora.strip()

    def __eq__(self, otra):
        # Dos franjas son iguales si coinciden en día y hora
        return self.dia == otra.dia and self.hora == otra.hora

    def __repr__(self):
        return f"{self.dia} {self.hora}"


class Profesor:
    def __init__(self, nombre, franjas_no_disponibles=None):
        self.nombre = nombre.strip()
        # Lista de objetos Franja donde el profesor prefiere no dar clase (restricción blanda)
        self.franjas_no_disponibles = franjas_no_disponibles if franjas_no_disponibles else []

    def __repr__(self):
        return f"Profesor({self.nombre})"


class Curso:
    def __init__(self, nombre, nombre_profesor, grupo):
        self.nombre = nombre.strip()
        self.nombre_profesor = nombre_profesor.strip()
        self.grupo = grupo.strip()

    def __repr__(self):
        return f"Curso({self.nombre}, Prof: {self.nombre_profesor}, Grupo: {self.grupo})"


class Asignacion:
    """Representa una clase ya programada en una franja y salón específicos."""
    def __init__(self, curso, franja, salon):
        self.curso = curso      # Objeto Curso
        self.franja = franja    # Objeto Franja
        self.salon = salon      # Objeto Salon

    def __repr__(self):
        return f"[{self.curso.nombre} -> {self.franja.dia} {self.franja.hora} en {self.salon.nombre}]"


class Nodo:
    """Representa un estado en el árbol de búsqueda."""
    def __init__(self, asignaciones=None, costo_g=0, heuristica_h=0):
        # Lista de objetos Asignacion que lleva este camino del árbol
        self.asignaciones = asignaciones if asignaciones else []
        self.costo_g = costo_g
        self.heuristica_h = heuristica_h

    @property
    def nivel(self):
        # El nivel del árbol es simplemente cuántos cursos llevamos asignados
        return len(self.asignaciones)

    @property
    def costo_f(self):
        # f(n) = g(n) + h(n) para el algoritmo A*
        return self.costo_g + self.heuristica_h

    def crear_hijo(self, nueva_asignacion, costo_paso=1, nueva_h=0):
        # Copiamos la lista de asignaciones del padre y agregamos la nueva
        nuevas_asignaciones = self.asignaciones.copy()
        nuevas_asignaciones.append(nueva_asignacion)
        return Nodo(
            asignaciones=nuevas_asignaciones,
            costo_g=self.costo_g + costo_paso,
            heuristica_h=nueva_h
        )