"""
Módulo interfaz.py
Agente UI Tkinter: Sistema de Asignación de Horarios Universitarios (CSP)

Implementación Integral:
- Paso 1: Ventana Principal, Estilos ttk y Panel de Carga de Archivos de Entrada.
- Paso 2: Panel de Configuración de Algoritmo y Control de Ejecución (Combobox y Botones).
- Paso 3: Tabla de Horario - Grilla Visual de Días vs. Franjas Horarias con Celdas Estilizadas.
- Paso 4: Panel de Estadísticas Comparativas (Treeview) y Bloque Principal de Arranque.
- Mejora UX: Contenedor con Scrollbar Vertical Global y soporte de rueda de ratón para
  navegar fluidamente por todos los paneles (incluyendo el Panel 4 de Estadísticas).
"""

import os
import sys

# Manejo amigable de la importación de Tkinter para entornos donde python3-tk deba ser instalado
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError as err:
    print("\n[ERROR DE DEPENDENCIAS]: Tkinter no se encuentra disponible en este intérprete.")
    print("En sistemas Debian/Ubuntu/Linux, instala el paquete ejecutando en terminal:")
    print("    sudo apt install -y python3-tk\n")
    raise err

# Importación de módulos lógicos del proyecto (sin modificarlos)
from cargador import (
    cargar_salones,
    cargar_franjas,
    cargar_profesores,
    cargar_cursos
)
from busqueda import (
    ProblemaHorario,
    busqueda_amplitud,
    busqueda_costo_uniforme,
    busqueda_profundidad_iterativa,
    busqueda_a_prima
)


class AplicacionHorarios(tk.Tk):
    """
    Ventana principal de la aplicación gráfica para la programación de horarios académicos.
    Integra el motor de búsqueda CSP con una visualización profesional en Tkinter.
    """

    def __init__(self):
        super().__init__()

        # -------------------------------------------------------------
        # 1. Configuración de la Ventana Principal
        # -------------------------------------------------------------
        self.title("Sistema de Asignación de Horarios Universitarios")
        self.geometry("1100x820")
        self.minsize(980, 680)
        self.configure(bg="#F1F5F9")  # Fondo general gris pizarra muy claro

        # -------------------------------------------------------------
        # 2. Estructuras de Datos en Memoria
        # -------------------------------------------------------------
        self.datos_profesores = []
        self.datos_cursos = []
        self.datos_salones = []
        self.datos_franjas = []

        self.ultimo_resultado = None
        self.ultimo_algoritmo = ""

        # Diccionario para almacenar rutas y referencias a widgets de estado
        self.archivos_info = {
            "profesores": {
                "nombre_mostrar": "Profesores (profesores.txt):",
                "ruta_var": tk.StringVar(value="Ningún archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "widget_estado": None,
                "funcion_carga": cargar_profesores
            },
            "cursos": {
                "nombre_mostrar": "Cursos / Materias (cursos.txt):",
                "ruta_var": tk.StringVar(value="Ningún archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "widget_estado": None,
                "funcion_carga": cargar_cursos
            },
            "salones": {
                "nombre_mostrar": "Salones (salones.txt):",
                "ruta_var": tk.StringVar(value="Ningún archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "widget_estado": None,
                "funcion_carga": cargar_salones
            },
            "franjas": {
                "nombre_mostrar": "Franjas Horarias (franjas.txt):",
                "ruta_var": tk.StringVar(value="Ningún archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "widget_estado": None,
                "funcion_carga": cargar_franjas
            }
        }

        # -------------------------------------------------------------
        # 3. Configuración de Estilos ttk ('clam' y paleta moderna)
        # -------------------------------------------------------------
        self.configurar_estilos()

        # -------------------------------------------------------------
        # 4. Banner Superior Institucional (Fijo)
        # -------------------------------------------------------------
        self.crear_banner_superior()

        # -------------------------------------------------------------
        # 5. Contenedor Global con Scrollbar Vertical para toda la Ventana
        # -------------------------------------------------------------
        self.marco_scroll_global = tk.Frame(self, bg="#F1F5F9")
        self.marco_scroll_global.pack(fill="both", expand=True)

        self.canvas_principal = tk.Canvas(
            self.marco_scroll_global,
            bg="#F1F5F9",
            highlightthickness=0
        )
        self.scrollbar_ventana = ttk.Scrollbar(
            self.marco_scroll_global,
            orient="vertical",
            command=self.canvas_principal.yview
        )
        self.canvas_principal.configure(yscrollcommand=self.scrollbar_ventana.set)

        self.scrollbar_ventana.pack(side="right", fill="y")
        self.canvas_principal.pack(side="left", fill="both", expand=True)

        # Marco interior alojado dentro del Canvas
        self.contenedor_principal = ttk.Frame(self.canvas_principal, style="Main.TFrame")
        self.window_principal_id = self.canvas_principal.create_window(
            (0, 0),
            window=self.contenedor_principal,
            anchor="nw"
        )

        # Ajuste dinámico de ancho y región de scroll
        self.contenedor_principal.bind(
            "<Configure>",
            self._ajustar_scrollregion_global
        )
        self.canvas_principal.bind(
            "<Configure>",
            self._ajustar_ancho_canvas
        )

        # Habilitar soporte de rueda de ratón (MouseWheel)
        self.habilitar_scroll_raton()

        # -------------------------------------------------------------
        # 6. Construcción de los 4 Paneles Principales
        # -------------------------------------------------------------
        # Panel 1: Carga de Archivos
        self.crear_panel_archivos()

        # Panel 2: Configuración de Algoritmo y Ejecución
        self.crear_panel_configuracion()

        # Panel 3: Horario Generado (Grilla Visual Dinámica)
        self.crear_panel_horario()

        # Panel 4: Estadísticas Comparativas de Rendimiento
        self.crear_panel_estadisticas()

    def _ajustar_scrollregion_global(self, event=None):
        """Actualiza el área desplazable del canvas principal."""
        self.canvas_principal.configure(scrollregion=self.canvas_principal.bbox("all"))

    def _ajustar_ancho_canvas(self, event):
        """Ajusta el ancho del marco interior para llenar el ancho disponible en la ventana."""
        self.canvas_principal.itemconfig(self.window_principal_id, width=event.width)

    def habilitar_scroll_raton(self):
        """
        Permite hacer scroll vertical con la rueda del ratón en Linux, Windows y macOS.
        """
        def _on_mousewheel(event):
            # En Linux se usan Button-4 (arriba) y Button-5 (abajo)
            if event.num == 4:
                self.canvas_principal.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas_principal.yview_scroll(1, "units")
            # En Windows y macOS se usa event.delta
            elif hasattr(event, 'delta') and event.delta:
                self.canvas_principal.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.bind_all("<Button-4>", _on_mousewheel)
        self.bind_all("<Button-5>", _on_mousewheel)
        self.bind_all("<MouseWheel>", _on_mousewheel)

    def configurar_estilos(self):
        """
        Configura el tema 'clam' de ttk y define una paleta visual limpia y profesional.
        """
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # Frames
        self.style.configure("Main.TFrame", background="#F1F5F9")
        self.style.configure("Card.TFrame", background="#FFFFFF")

        # LabelFrame para los paneles
        self.style.configure(
            "Card.TLabelframe",
            background="#FFFFFF",
            relief="solid",
            borderwidth=1
        )
        self.style.configure(
            "Card.TLabelframe.Label",
            background="#FFFFFF",
            foreground="#1E293B",
            font=("Segoe UI", 10, "bold")
        )

        # Botones de Carga de Archivo (Examinar)
        self.style.configure(
            "Examinar.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#E2E8F0",
            foreground="#1E293B",
            borderwidth=1,
            padding=(10, 4)
        )
        self.style.map(
            "Examinar.TButton",
            background=[("active", "#CBD5E1"), ("pressed", "#94A3B8")]
        )

        # Botón para precarga automática de pruebas
        self.style.configure(
            "Autocarga.TButton",
            font=("Segoe UI", 9),
            background="#F8FAFC",
            foreground="#475569",
            padding=(8, 3)
        )

        # Estilo del Combobox
        self.style.configure(
            "TCombobox",
            font=("Segoe UI", 10),
            padding=4
        )

        # Estilo de la tabla de estadísticas Treeview
        self.style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            fieldbackground="#FFFFFF",
            rowheight=26,
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "Treeview.Heading",
            background="#1E293B",
            foreground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=5
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", "#334155")]
        )

    def crear_banner_superior(self):
        """
        Crea el encabezado superior institucional en azul oscuro ejecutivo (#1E293B).
        """
        banner = tk.Frame(self, bg="#1E293B", height=65)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)

        contenedor_texto = tk.Frame(banner, bg="#1E293B")
        contenedor_texto.pack(fill="both", expand=True, padx=24, pady=8)

        titulo = tk.Label(
            contenedor_texto,
            text="PROGRAMACIÓN ACADÉMICA UNIVERSITARIA",
            bg="#1E293B",
            fg="#FFFFFF",
            font=("Segoe UI", 15, "bold")
        )
        titulo.pack(anchor="w")

        subtitulo = tk.Label(
            contenedor_texto,
            text="Sistema de Asignación y Optimización de Horarios mediante Búsqueda CSP",
            bg="#1E293B",
            fg="#94A3B8",
            font=("Segoe UI", 9)
        )
        subtitulo.pack(anchor="w")

    def crear_panel_archivos(self):
        """
        Construye el Panel 1: Carga de Archivos (.txt) para profesores, cursos, salones y franjas.
        """
        labelframe = ttk.LabelFrame(
            self.contenedor_principal,
            text="  1. Carga de Archivos de Entrada (.txt)  ",
            style="Card.TLabelframe"
        )
        labelframe.pack(fill="x", padx=20, pady=(12, 10))

        marco_interior = tk.Frame(labelframe, bg="#FFFFFF", padx=15, pady=8)
        marco_interior.pack(fill="x", expand=True)

        marco_interior.columnconfigure(0, minsize=190)
        marco_interior.columnconfigure(1, minsize=110)
        marco_interior.columnconfigure(2, weight=1)
        marco_interior.columnconfigure(3, minsize=230)

        orden_archivos = ["profesores", "cursos", "salones", "franjas"]

        for fila, clave in enumerate(orden_archivos):
            info = self.archivos_info[clave]

            lbl_nombre = tk.Label(
                marco_interior,
                text=info["nombre_mostrar"],
                font=("Segoe UI", 9, "bold"),
                bg="#FFFFFF",
                fg="#334155",
                anchor="w"
            )
            lbl_nombre.grid(row=fila, column=0, sticky="w", pady=3)

            btn_examinar = ttk.Button(
                marco_interior,
                text="Examinar...",
                style="Examinar.TButton",
                command=lambda k=clave: self.examinar_archivo(k)
            )
            btn_examinar.grid(row=fila, column=1, sticky="w", padx=8, pady=3)

            lbl_ruta = tk.Label(
                marco_interior,
                textvariable=info["ruta_var"],
                font=("Segoe UI", 8),
                bg="#F8FAFC",
                fg="#64748B",
                anchor="w",
                relief="solid",
                borderwidth=1,
                padx=8,
                pady=2
            )
            lbl_ruta.grid(row=fila, column=2, sticky="ew", padx=8, pady=3)

            lbl_estado = tk.Label(
                marco_interior,
                textvariable=info["estado_var"],
                font=("Segoe UI", 9, "bold"),
                bg="#FFFFFF",
                fg="#64748B",
                anchor="w"
            )
            lbl_estado.grid(row=fila, column=3, sticky="w", padx=6, pady=3)
            info["widget_estado"] = lbl_estado

        fila_extra = len(orden_archivos)
        marco_pie = tk.Frame(marco_interior, bg="#FFFFFF")
        marco_pie.grid(row=fila_extra, column=0, columnspan=4, sticky="ew", pady=(6, 2))

        btn_autocarga = ttk.Button(
            marco_pie,
            text="⚡ Cargar archivos de prueba automáticamente (carpeta datos/)",
            style="Autocarga.TButton",
            command=self.autocargar_archivos_prueba
        )
        btn_autocarga.pack(side="right")

    def crear_panel_configuracion(self):
        """
        Construye el Panel 2: Selección de Algoritmo y Botón 'Generar Horario'.
        """
        labelframe = ttk.LabelFrame(
            self.contenedor_principal,
            text="  2. Configuración del Algoritmo y Ejecución  ",
            style="Card.TLabelframe"
        )
        labelframe.pack(fill="x", padx=20, pady=(0, 10))

        marco_interior = tk.Frame(labelframe, bg="#FFFFFF", padx=15, pady=10)
        marco_interior.pack(fill="x", expand=True)

        lbl_algoritmo = tk.Label(
            marco_interior,
            text="Algoritmo de búsqueda:",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        )
        lbl_algoritmo.pack(side="left", padx=(0, 10))

        self.opciones_algoritmos = [
            "Búsqueda en Amplitud (BFS)",
            "Búsqueda de Costo Uniforme (UCS)",
            "Profundidad Iterativa (IDDFS)",
            "A* (Informado)"
        ]
        self.combo_algoritmo = ttk.Combobox(
            marco_interior,
            values=self.opciones_algoritmos,
            state="readonly",
            width=32,
            style="TCombobox"
        )
        self.combo_algoritmo.current(3)
        self.combo_algoritmo.pack(side="left", padx=(0, 15))

        # Botón Principal "Generar Horario"
        self.btn_generar = tk.Button(
            marco_interior,
            text="▶ Generar Horario",
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=5,
            command=self.ejecutar_busqueda
        )
        self.btn_generar.pack(side="left", padx=(0, 10))
        self.btn_generar.bind("<Enter>", lambda e: self.btn_generar.configure(bg="#1D4ED8"))
        self.btn_generar.bind("<Leave>", lambda e: self.btn_generar.configure(bg="#2563EB"))

        # Botón Secundario "Comparar Todos"
        self.btn_comparar = tk.Button(
            marco_interior,
            text="⚡ Comparar Todos",
            bg="#475569",
            fg="#FFFFFF",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=5,
            command=self.comparar_todos
        )
        self.btn_comparar.pack(side="left", padx=(0, 15))
        self.btn_comparar.bind("<Enter>", lambda e: self.btn_comparar.configure(bg="#334155"))
        self.btn_comparar.bind("<Leave>", lambda e: self.btn_comparar.configure(bg="#475569"))

        # Indicador de estado del proceso
        self.lbl_estado_busqueda = tk.Label(
            marco_interior,
            text="Listo para ejecutar.",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#64748B",
            anchor="w"
        )
        self.lbl_estado_busqueda.pack(side="left", fill="x", expand=True)

    def crear_panel_horario(self):
        """
        Construye el Panel 3: HORARIO GENERADO con un contenedor con scroll horizontal responsivo.
        """
        self.labelframe_horario = ttk.LabelFrame(
            self.contenedor_principal,
            text="  3. Horario Generado (Matriz Días vs. Franjas Horarias)  ",
            style="Card.TLabelframe"
        )
        self.labelframe_horario.pack(fill="x", padx=20, pady=(0, 10))

        # Contenedor interior con scroll horizontal para días/columnas anchas
        marco_contenedor_grilla = tk.Frame(self.labelframe_horario, bg="#FFFFFF")
        marco_contenedor_grilla.pack(fill="x", expand=True, padx=8, pady=8)

        self.canvas_horario = tk.Canvas(
            marco_contenedor_grilla,
            bg="#FFFFFF",
            highlightthickness=0,
            height=280
        )
        self.scrollbar_x = ttk.Scrollbar(
            marco_contenedor_grilla,
            orient="horizontal",
            command=self.canvas_horario.xview
        )
        self.canvas_horario.configure(xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_x.pack(side="bottom", fill="x")
        self.canvas_horario.pack(side="top", fill="both", expand=True)

        self.marco_grilla = tk.Frame(self.canvas_horario, bg="#FFFFFF", padx=6, pady=6)
        self.window_canvas_id = self.canvas_horario.create_window(
            (0, 0),
            window=self.marco_grilla,
            anchor="nw"
        )

        self.marco_grilla.bind(
            "<Configure>",
            self._ajustar_scroll_grilla
        )

        self.mostrar_mensaje_inicial_grilla()

    def _ajustar_scroll_grilla(self, event=None):
        """Ajusta la región de desplazamiento del canvas del horario y del canvas global."""
        bbox = self.canvas_horario.bbox("all")
        if bbox:
            altura_grilla = bbox[3] - bbox[1]
            # Ajustar la altura visible del canvas si la grilla es menor o mayor
            self.canvas_horario.configure(
                scrollregion=bbox,
                height=min(max(altura_grilla + 10, 120), 400)
            )
        self._ajustar_scrollregion_global()

    def mostrar_mensaje_inicial_grilla(self):
        """
        Muestra un mensaje informativo cuando aún no se ha generado ningún horario.
        """
        for w in self.marco_grilla.winfo_children():
            w.destroy()

        lbl_vacio = tk.Label(
            self.marco_grilla,
            text="📌 Carga los archivos y haz clic en 'Generar Horario' para visualizar la grilla académica.",
            font=("Segoe UI", 10, "italic"),
            bg="#FFFFFF",
            fg="#94A3B8",
            padx=20,
            pady=30
        )
        lbl_vacio.pack(fill="both", expand=True)

    def dibujar_grilla_horario(self, nodo_solucion):
        """
        Construye dinámicamente la matriz de horarios (Filas: Horas, Columnas: Días).
        
        Args:
            nodo_solucion (Nodo): Nodo meta con la lista de asignaciones programadas.
        """
        for widget in self.marco_grilla.winfo_children():
            widget.destroy()

        if not nodo_solucion or not nodo_solucion.asignaciones:
            self.mostrar_mensaje_inicial_grilla()
            return

        # 1. Obtener lista de Días
        dias = []
        if self.datos_franjas:
            for f in self.datos_franjas:
                if f.dia not in dias:
                    dias.append(f.dia)
        else:
            for asig in nodo_solucion.asignaciones:
                if asig.franja.dia not in dias:
                    dias.append(asig.franja.dia)

        # 2. Obtener lista de Horas
        horas = []
        if self.datos_franjas:
            for f in self.datos_franjas:
                if f.hora not in horas:
                    horas.append(f.hora)
        else:
            for asig in nodo_solucion.asignaciones:
                if asig.franja.hora not in horas:
                    horas.append(asig.franja.hora)

        self.marco_grilla.columnconfigure(0, minsize=110)
        for c in range(1, len(dias) + 1):
            self.marco_grilla.columnconfigure(c, minsize=190, weight=1)

        # 3. Celda de Esquina
        lbl_esquina = tk.Label(
            self.marco_grilla,
            text="BLOQUE / DÍA",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=8
        )
        lbl_esquina.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        # 4. Encabezados de Días
        for c_idx, dia in enumerate(dias, start=1):
            lbl_dia = tk.Label(
                self.marco_grilla,
                text=dia.upper(),
                font=("Segoe UI", 10, "bold"),
                bg="#334155",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=8
            )
            lbl_dia.grid(row=0, column=c_idx, sticky="nsew", padx=1, pady=1)

        # 5. Filas de Horas y Celdas de Asignación
        for r_idx, hora in enumerate(horas, start=1):
            lbl_hora = tk.Label(
                self.marco_grilla,
                text=hora,
                font=("Segoe UI", 9, "bold"),
                bg="#334155",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=8,
                pady=10
            )
            lbl_hora.grid(row=r_idx, column=0, sticky="nsew", padx=1, pady=1)

            for c_idx, dia in enumerate(dias, start=1):
                clases_en_celda = [
                    asig for asig in nodo_solucion.asignaciones
                    if asig.franja.dia == dia and asig.franja.hora == hora
                ]

                if clases_en_celda:
                    celda_frame = tk.Frame(
                        self.marco_grilla,
                        bg="#DBEAFE",
                        highlightbackground="#93C5FD",
                        highlightthickness=1,
                        padx=6,
                        pady=6
                    )
                    celda_frame.grid(row=r_idx, column=c_idx, sticky="nsew", padx=2, pady=2)

                    for i, asig in enumerate(clases_en_celda):
                        if i > 0:
                            sep = tk.Frame(celda_frame, bg="#BFDBFE", height=1)
                            sep.pack(fill="x", pady=4)

                        lbl_materia = tk.Label(
                            celda_frame,
                            text=f"📚 {asig.curso.nombre}",
                            font=("Segoe UI", 9, "bold"),
                            bg="#DBEAFE",
                            fg="#1E3A8A",
                            anchor="w"
                        )
                        lbl_materia.pack(fill="x", anchor="w")

                        lbl_prof = tk.Label(
                            celda_frame,
                            text=f"👨‍🏫 {asig.curso.nombre_profesor}",
                            font=("Segoe UI", 8),
                            bg="#DBEAFE",
                            fg="#1E293B",
                            anchor="w"
                        )
                        lbl_prof.pack(fill="x", anchor="w")

                        lbl_detalles = tk.Label(
                            celda_frame,
                            text=f"📍 {asig.salon.nombre} | 👥 {asig.curso.grupo}",
                            font=("Segoe UI", 8, "italic"),
                            bg="#DBEAFE",
                            fg="#2563EB",
                            anchor="w"
                        )
                        lbl_detalles.pack(fill="x", anchor="w")

                else:
                    celda_libre = tk.Frame(
                        self.marco_grilla,
                        bg="#F8FAFC",
                        highlightbackground="#E2E8F0",
                        highlightthickness=1,
                        padx=6,
                        pady=12
                    )
                    celda_libre.grid(row=r_idx, column=c_idx, sticky="nsew", padx=2, pady=2)

                    lbl_libre = tk.Label(
                        celda_libre,
                        text="---",
                        font=("Segoe UI", 9),
                        bg="#F8FAFC",
                        fg="#94A3B8"
                    )
                    lbl_libre.pack(expand=True)

        self._ajustar_scroll_grilla()

    def crear_panel_estadisticas(self):
        """
        Construye el Panel 4: ESTADÍSTICAS COMPARATIVAS usando un ttk.Treeview.
        Muestra la comparación de rendimiento (nodos, tiempo, costo, solución) de los 4 algoritmos.
        """
        self.labelframe_stats = ttk.LabelFrame(
            self.contenedor_principal,
            text="  4. Estadísticas Comparativas de Rendimiento  ",
            style="Card.TLabelframe"
        )
        self.labelframe_stats.pack(fill="x", padx=20, pady=(0, 25))

        marco_interior = tk.Frame(self.labelframe_stats, bg="#FFFFFF", padx=15, pady=8)
        marco_interior.pack(fill="x", expand=True)

        # Definición de columnas
        columnas = ("algoritmo", "nodos", "tiempo", "costo", "solucion")
        self.tabla_stats = ttk.Treeview(
            marco_interior,
            columns=columnas,
            show="headings",
            height=4,
            style="Treeview"
        )

        # Encabezados y anchos
        self.tabla_stats.heading("algoritmo", text="Algoritmo de Búsqueda", anchor="w")
        self.tabla_stats.heading("nodos", text="Nodos Explorados", anchor="center")
        self.tabla_stats.heading("tiempo", text="Tiempo (s)", anchor="center")
        self.tabla_stats.heading("costo", text="Costo Total g(n)", anchor="center")
        self.tabla_stats.heading("solucion", text="¿Solución Encontrada?", anchor="center")

        self.tabla_stats.column("algoritmo", width=280, anchor="w")
        self.tabla_stats.column("nodos", width=160, anchor="center")
        self.tabla_stats.column("tiempo", width=150, anchor="center")
        self.tabla_stats.column("costo", width=140, anchor="center")
        self.tabla_stats.column("solucion", width=160, anchor="center")

        self.tabla_stats.pack(fill="x", expand=True)

        # Mapeo de algoritmos para el identificador de fila (iid)
        self.algoritmos_referencia = [
            ("BFS", "Búsqueda en Amplitud (BFS)"),
            ("UCS", "Búsqueda de Costo Uniforme (UCS)"),
            ("IDDFS", "Profundidad Iterativa (IDDFS)"),
            ("A*", "A* (Informado)")
        ]

        # Inicializar las 4 filas como 'Pendiente'
        for iid, nombre_largo in self.algoritmos_referencia:
            self.tabla_stats.insert(
                "",
                "end",
                iid=iid,
                values=(nombre_largo, "---", "---", "---", "⚪ Sin ejecutar")
            )

    def actualizar_estadistica(self, nombre_algoritmo, resultado):
        """
        Inserta o actualiza en tiempo real la fila correspondiente al algoritmo ejecutado
        dentro de la tabla Treeview sin borrar las demás métricas previas.
        
        Args:
            nombre_algoritmo (str): Identificador corto ('BFS', 'UCS', 'IDDFS', 'A*').
            resultado (ResultadoBusqueda): Objeto con las métricas devueltas por el algoritmo.
        """
        nombre_completo = {
            "BFS": "Búsqueda en Amplitud (BFS)",
            "UCS": "Búsqueda de Costo Uniforme (UCS)",
            "IDDFS": "Profundidad Iterativa (IDDFS)",
            "A*": "A* (Informado)"
        }.get(nombre_algoritmo, nombre_algoritmo)

        nodos_str = f"{resultado.nodos_explorados:,}"
        tiempo_str = f"{resultado.tiempo_segundos:.6f} s"

        if resultado.encontro_solucion:
            solucion_str = "✔ Sí (Óptima)" if resultado.nodo_solucion.costo_g <= 4 else "✔ Sí"
            costo_str = str(resultado.nodo_solucion.costo_g)
        else:
            solucion_str = "✖ No"
            costo_str = "N/A"

        nuevos_valores = (nombre_completo, nodos_str, tiempo_str, costo_str, solucion_str)

        if self.tabla_stats.exists(nombre_algoritmo):
            self.tabla_stats.item(nombre_algoritmo, values=nuevos_valores)
        else:
            self.tabla_stats.insert("", "end", iid=nombre_algoritmo, values=nuevos_valores)

    def ejecutar_busqueda(self):
        """
        Valida que los 4 archivos estén cargados, instancia ProblemaHorario,
        ejecuta el algoritmo seleccionado y actualiza la visualización de la grilla y estadísticas.
        """
        if not (self.datos_profesores and self.datos_cursos and self.datos_salones and self.datos_franjas):
            faltantes = []
            if not self.datos_profesores: faltantes.append("Profesores")
            if not self.datos_cursos: faltantes.append("Cursos")
            if not self.datos_salones: faltantes.append("Salones")
            if not self.datos_franjas: faltantes.append("Franjas")

            messagebox.showwarning(
                "Archivos Faltantes",
                f"Debe cargar los 4 archivos antes de generar el horario.\n\nFaltan por cargar:\n• " +
                "\n• ".join(faltantes)
            )
            return

        seleccion = self.combo_algoritmo.get()

        mapa_algoritmos = {
            "Búsqueda en Amplitud (BFS)": ("BFS", busqueda_amplitud),
            "Búsqueda de Costo Uniforme (UCS)": ("UCS", busqueda_costo_uniforme),
            "Profundidad Iterativa (IDDFS)": ("IDDFS", busqueda_profundidad_iterativa),
            "A* (Informado)": ("A*", busqueda_a_prima)
        }

        if seleccion not in mapa_algoritmos:
            messagebox.showerror("Error", "Algoritmo seleccionado no válido.")
            return

        nombre_corto, funcion_algoritmo = mapa_algoritmos[seleccion]

        self.lbl_estado_busqueda.configure(
            text=f"⏳ Ejecutando {nombre_corto}...",
            fg="#2563EB"
        )
        self.update_idletasks()

        problema = ProblemaHorario(
            cursos=self.datos_cursos,
            profesores=self.datos_profesores,
            salones=self.datos_salones,
            franjas=self.datos_franjas,
            max_consecutivas=2
        )

        resultado = funcion_algoritmo(problema)
        self.ultimo_resultado = resultado
        self.ultimo_algoritmo = nombre_corto

        if resultado.encontro_solucion:
            self.lbl_estado_busqueda.configure(
                text=f"✔ {nombre_corto} completado: {resultado.tiempo_segundos:.4f}s | "
                     f"{resultado.nodos_explorados} nodos | Costo g(n): {resultado.nodo_solucion.costo_g}",
                fg="#16A34A"
            )
            self.actualizar_horario(resultado.nodo_solucion)
            self.actualizar_estadistica(nombre_corto, resultado)
        else:
            self.lbl_estado_busqueda.configure(
                text=f"✖ {nombre_corto} no encontró solución válida ({resultado.tiempo_segundos:.4f}s).",
                fg="#DC2626"
            )
            self.actualizar_estadistica(nombre_corto, resultado)
            messagebox.showinfo(
                "Sin Solución",
                "El algoritmo no pudo encontrar una asignación que satisfaga todas las restricciones duras."
            )

    def comparar_todos(self):
        """
        Ejecuta secuencialmente los 4 algoritmos, actualiza la tabla comparativa de estadísticas
        y muestra la grilla del mejor horario encontrado.
        """
        if not (self.datos_profesores and self.datos_cursos and self.datos_salones and self.datos_franjas):
            messagebox.showwarning(
                "Archivos Faltantes",
                "Debe cargar los 4 archivos de entrada para realizar la comparativa."
            )
            return

        algoritmos_a_correr = [
            ("BFS", busqueda_amplitud),
            ("UCS", busqueda_costo_uniforme),
            ("IDDFS", busqueda_profundidad_iterativa),
            ("A*", busqueda_a_prima)
        ]

        mejor_solucion = None
        mejor_costo = float("inf")

        for nombre_corto, funcion in algoritmos_a_correr:
            problema = ProblemaHorario(
                cursos=self.datos_cursos,
                profesores=self.datos_profesores,
                salones=self.datos_salones,
                franjas=self.datos_franjas,
                max_consecutivas=2
            )
            res = funcion(problema)
            self.actualizar_estadistica(nombre_corto, res)

            if res.encontro_solucion and res.nodo_solucion.costo_g < mejor_costo:
                mejor_costo = res.nodo_solucion.costo_g
                mejor_solucion = res.nodo_solucion

        if mejor_solucion:
            self.actualizar_horario(mejor_solucion)
            self.lbl_estado_busqueda.configure(
                text=f"✔ Comparativa finalizada. Mostrando mejor solución (Costo: {mejor_costo}).",
                fg="#16A34A"
            )

    def actualizar_horario(self, nodo_solucion):
        """
        Actualiza la grilla visual del horario con el nodo solución.
        """
        self.dibujar_grilla_horario(nodo_solucion)

    def examinar_archivo(self, clave):
        """
        Abre el explorador de archivos nativo del SO para seleccionar un archivo .txt.
        """
        ruta = filedialog.askopenfilename(
            title=f"Seleccionar archivo de {clave}",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            self.procesar_archivo(clave, ruta)

    def procesar_archivo(self, clave, ruta):
        """
        Lee el archivo usando la función correspondiente de cargador.py,
        actualiza la ruta visual y cambia el estado a verde o rojo según el resultado.
        """
        info = self.archivos_info[clave]
        info["ruta_var"].set(ruta)

        try:
            funcion = info["funcion_carga"]
            datos = funcion(ruta)

            if datos and len(datos) > 0:
                if clave == "profesores":
                    self.datos_profesores = datos
                    etiqueta_tipo = "profesores"
                elif clave == "cursos":
                    self.datos_cursos = datos
                    etiqueta_tipo = "cursos"
                elif clave == "salones":
                    self.datos_salones = datos
                    etiqueta_tipo = "salones"
                elif clave == "franjas":
                    self.datos_franjas = datos
                    etiqueta_tipo = "franjas"

                info["estado_var"].set(f"✔ Leído correctamente ({len(datos)} {etiqueta_tipo})")
                if info["widget_estado"]:
                    info["widget_estado"].configure(fg="#16A34A")
            else:
                info["estado_var"].set("✖ Archivo vacío (0 registros)")
                if info["widget_estado"]:
                    info["widget_estado"].configure(fg="#DC2626")

        except Exception as e:
            info["estado_var"].set("✖ Error de formato")
            if info["widget_estado"]:
                info["widget_estado"].configure(fg="#DC2626")
            messagebox.showerror(
                "Error de Carga",
                f"No se pudo procesar el archivo '{os.path.basename(ruta)}':\n{e}"
            )

    def autocargar_archivos_prueba(self):
        """
        Busca y carga automáticamente los archivos salones.txt, franjas.txt,
        profesores.txt y cursos.txt dentro de la carpeta 'datos' si existen.
        """
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        carpeta_datos = os.path.join(directorio_actual, "datos")

        mapa_archivos = {
            "profesores": "profesores.txt",
            "cursos": "cursos.txt",
            "salones": "salones.txt",
            "franjas": "franjas.txt"
        }

        todos_existen = True
        for clave, nombre_archivo in mapa_archivos.items():
            ruta_completa = os.path.join(carpeta_datos, nombre_archivo)
            if os.path.exists(ruta_completa):
                self.procesar_archivo(clave, ruta_completa)
            else:
                todos_existen = False

        if not todos_existen:
            messagebox.showwarning(
                "Archivos no encontrados",
                f"No se encontraron todos los archivos de prueba en:\n{carpeta_datos}"
            )


# =====================================================================
# BLOQUE PRINCIPAL DE ARRANQUE DE LA APLICACIÓN
# =====================================================================
if __name__ == "__main__":
    app = AplicacionHorarios()
    app.mainloop()
