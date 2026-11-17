import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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


# Ventana principal de la aplicacion
class AplicacionHorarios(tk.Tk):
    def __init__(self):
        super().__init__()

        # configuracion de la ventana
        self.title("Sistema de Asignacion de Horarios Universitarios")
        self.geometry("1100x820")
        self.minsize(980, 680)
        self.configure(bg="#F1F5F9")

        # datos cargados en memoria
        self.profesores = []
        self.cursos = []
        self.salones = []
        self.franjas = []

        self.ultimo_resultado = None
        self.ultimo_algoritmo = ""

        # diccionario para manejar los archivos de entrada
        self.archivos = {
            "profesores": {
                "nombre": "Profesores (profesores.txt):",
                "ruta_var": tk.StringVar(value="Ningun archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "lbl_estado": None,
                "funcion": cargar_profesores
            },
            "cursos": {
                "nombre": "Cursos / Materias (cursos.txt):",
                "ruta_var": tk.StringVar(value="Ningun archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "lbl_estado": None,
                "funcion": cargar_cursos
            },
            "salones": {
                "nombre": "Salones (salones.txt):",
                "ruta_var": tk.StringVar(value="Ningun archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "lbl_estado": None,
                "funcion": cargar_salones
            },
            "franjas": {
                "nombre": "Franjas Horarias (franjas.txt):",
                "ruta_var": tk.StringVar(value="Ningun archivo seleccionado"),
                "estado_var": tk.StringVar(value="⚪ Pendiente de cargar"),
                "lbl_estado": None,
                "funcion": cargar_franjas
            }
        }

        # configurar estilos de ttk
        self.configurar_estilos()

        # encabezado
        self.crear_banner_superior()

        # contenedor con scrollbar para toda la ventana
        self.frame_scroll = tk.Frame(self, bg="#F1F5F9")
        self.frame_scroll.pack(fill="both", expand=True)

        self.canvas_principal = tk.Canvas(
            self.frame_scroll,
            bg="#F1F5F9",
            highlightthickness=0
        )
        self.scroll_y = ttk.Scrollbar(
            self.frame_scroll,
            orient="vertical",
            command=self.canvas_principal.yview
        )
        self.canvas_principal.configure(yscrollcommand=self.scroll_y.set)

        self.scroll_y.pack(side="right", fill="y")
        self.canvas_principal.pack(side="left", fill="both", expand=True)

        self.contenedor = ttk.Frame(self.canvas_principal, style="Main.TFrame")
        self.window_id = self.canvas_principal.create_window(
            (0, 0),
            window=self.contenedor,
            anchor="nw"
        )

        # actualizar tamaño del canvas al cambiar la ventana
        self.contenedor.bind(
            "<Configure>",
            lambda e: self.canvas_principal.configure(scrollregion=self.canvas_principal.bbox("all"))
        )
        self.canvas_principal.bind(
            "<Configure>",
            lambda e: self.canvas_principal.itemconfig(self.window_id, width=e.width)
        )

        # rueda del raton
        self.habilitar_scroll_raton()

        # paneles de la interfaz
        self.crear_panel_archivos()
        self.crear_panel_configuracion()
        self.crear_panel_horario()
        self.crear_panel_estadisticas()

    # permite hacer scroll con la rueda del raton
    def habilitar_scroll_raton(self):
        def _on_mousewheel(event):
            if event.num == 4:
                self.canvas_principal.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas_principal.yview_scroll(1, "units")
            elif hasattr(event, 'delta') and event.delta:
                self.canvas_principal.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.bind_all("<Button-4>", _on_mousewheel)
        self.bind_all("<Button-5>", _on_mousewheel)
        self.bind_all("<MouseWheel>", _on_mousewheel)

    # estilos para botones, tablas y tarjetas
    def configurar_estilos(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self.style.configure("Main.TFrame", background="#F1F5F9")
        self.style.configure("Card.TFrame", background="#FFFFFF")

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

        # botones examinar
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

        # boton de carga de prueba
        self.style.configure(
            "Autocarga.TButton",
            font=("Segoe UI", 9),
            background="#F8FAFC",
            foreground="#475569",
            padding=(8, 3)
        )

        self.style.configure(
            "TCombobox",
            font=("Segoe UI", 10),
            padding=4
        )

        # tabla de estadisticas
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

    # banner superior
    def crear_banner_superior(self):
        banner = tk.Frame(self, bg="#1E293B", height=65)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)

        texto_frame = tk.Frame(banner, bg="#1E293B")
        texto_frame.pack(fill="both", expand=True, padx=24, pady=8)

        titulo = tk.Label(
            texto_frame,
            text="PROGRAMACIÓN ACADÉMICA UNIVERSITARIA",
            bg="#1E293B",
            fg="#FFFFFF",
            font=("Segoe UI", 15, "bold")
        )
        titulo.pack(anchor="w")

        subtitulo = tk.Label(
            texto_frame,
            text="Sistema de Asignacion de Horarios con Algoritmos de Busqueda (CSP)",
            bg="#1E293B",
            fg="#94A3B8",
            font=("Segoe UI", 9)
        )
        subtitulo.pack(anchor="w")

    # panel 1: carga de archivos txt
    def crear_panel_archivos(self):
        labelframe = ttk.LabelFrame(
            self.contenedor,
            text="  1. Carga de Archivos de Entrada (.txt)  ",
            style="Card.TLabelframe"
        )
        labelframe.pack(fill="x", padx=20, pady=(12, 10))

        marco = tk.Frame(labelframe, bg="#FFFFFF", padx=15, pady=8)
        marco.pack(fill="x", expand=True)

        marco.columnconfigure(0, minsize=190)
        marco.columnconfigure(1, minsize=110)
        marco.columnconfigure(2, weight=1)
        marco.columnconfigure(3, minsize=230)

        orden = ["profesores", "cursos", "salones", "franjas"]

        for fila, clave in enumerate(orden):
            info = self.archivos[clave]

            lbl_nombre = tk.Label(
                marco,
                text=info["nombre"],
                font=("Segoe UI", 9, "bold"),
                bg="#FFFFFF",
                fg="#334155",
                anchor="w"
            )
            lbl_nombre.grid(row=fila, column=0, sticky="w", pady=3)

            btn = ttk.Button(
                marco,
                text="Examinar...",
                style="Examinar.TButton",
                command=lambda k=clave: self.examinar_archivo(k)
            )
            btn.grid(row=fila, column=1, sticky="w", padx=8, pady=3)

            lbl_ruta = tk.Label(
                marco,
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
                marco,
                textvariable=info["estado_var"],
                font=("Segoe UI", 9, "bold"),
                bg="#FFFFFF",
                fg="#64748B",
                anchor="w"
            )
            lbl_estado.grid(row=fila, column=3, sticky="w", padx=6, pady=3)
            info["lbl_estado"] = lbl_estado

        # boton para cargar rapido los txt de prueba
        fila_extra = len(orden)
        pie = tk.Frame(marco, bg="#FFFFFF")
        pie.grid(row=fila_extra, column=0, columnspan=4, sticky="ew", pady=(6, 2))

        btn_autocarga = ttk.Button(
            pie,
            text="⚡ Cargar archivos de prueba automaticamente (carpeta datos/)",
            style="Autocarga.TButton",
            command=self.autocargar_archivos_prueba
        )
        btn_autocarga.pack(side="right")

    # panel 2: selector de algoritmo y boton generar
    def crear_panel_configuracion(self):
        labelframe = ttk.LabelFrame(
            self.contenedor,
            text="  2. Configuracion del Algoritmo y Ejecucion  ",
            style="Card.TLabelframe"
        )
        labelframe.pack(fill="x", padx=20, pady=(0, 10))

        marco = tk.Frame(labelframe, bg="#FFFFFF", padx=15, pady=10)
        marco.pack(fill="x", expand=True)

        lbl = tk.Label(
            marco,
            text="Algoritmo de busqueda:",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#1E293B"
        )
        lbl.pack(side="left", padx=(0, 10))

        self.opciones_algoritmos = [
            "Búsqueda en Amplitud (BFS)",
            "Búsqueda de Costo Uniforme (UCS)",
            "Profundidad Iterativa (IDDFS)",
            "A* (Informado)"
        ]
        self.combo_algoritmo = ttk.Combobox(
            marco,
            values=self.opciones_algoritmos,
            state="readonly",
            width=32,
            style="TCombobox"
        )
        self.combo_algoritmo.current(3)
        self.combo_algoritmo.pack(side="left", padx=(0, 15))

        # boton principal
        self.btn_generar = tk.Button(
            marco,
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

        # boton para correr todos
        self.btn_comparar = tk.Button(
            marco,
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

        self.lbl_estado_busqueda = tk.Label(
            marco,
            text="Listo para ejecutar.",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#64748B",
            anchor="w"
        )
        self.lbl_estado_busqueda.pack(side="left", fill="x", expand=True)

    # panel 3: matriz del horario generado
    def crear_panel_horario(self):
        self.labelframe_horario = ttk.LabelFrame(
            self.contenedor,
            text="  3. Horario Generado (Matriz Dias vs. Franjas Horarias)  ",
            style="Card.TLabelframe"
        )
        self.labelframe_horario.pack(fill="x", padx=20, pady=(0, 10))

        marco_grilla = tk.Frame(self.labelframe_horario, bg="#FFFFFF")
        marco_grilla.pack(fill="x", expand=True, padx=8, pady=8)

        self.canvas_horario = tk.Canvas(
            marco_grilla,
            bg="#FFFFFF",
            highlightthickness=0,
            height=280
        )
        self.scrollbar_x = ttk.Scrollbar(
            marco_grilla,
            orient="horizontal",
            command=self.canvas_horario.xview
        )
        self.canvas_horario.configure(xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_x.pack(side="bottom", fill="x")
        self.canvas_horario.pack(side="top", fill="both", expand=True)

        self.marco_tabla = tk.Frame(self.canvas_horario, bg="#FFFFFF", padx=6, pady=6)
        self.canvas_horario.create_window(
            (0, 0),
            window=self.marco_tabla,
            anchor="nw"
        )

        self.marco_tabla.bind(
            "<Configure>",
            self._ajustar_scroll_grilla
        )

        self.mostrar_mensaje_inicial_grilla()

    # ajusta la altura visible de la grilla
    def _ajustar_scroll_grilla(self, event=None):
        bbox = self.canvas_horario.bbox("all")
        if bbox:
            altura = bbox[3] - bbox[1]
            self.canvas_horario.configure(
                scrollregion=bbox,
                height=min(max(altura + 10, 120), 400)
            )
        self.canvas_principal.configure(scrollregion=self.canvas_principal.bbox("all"))

    # mensaje informativo cuando no hay horario aun
    def mostrar_mensaje_inicial_grilla(self):
        for w in self.marco_tabla.winfo_children():
            w.destroy()

        lbl = tk.Label(
            self.marco_tabla,
            text="📌 Carga los archivos y haz clic en 'Generar Horario' para visualizar la grilla academica.",
            font=("Segoe UI", 10, "italic"),
            bg="#FFFFFF",
            fg="#94A3B8",
            padx=20,
            pady=30
        )
        lbl.pack(fill="both", expand=True)

    # dibuja la grilla con los cursos asignados
    def dibujar_grilla_horario(self, nodo_solucion):
        for w in self.marco_tabla.winfo_children():
            w.destroy()

        if not nodo_solucion or not nodo_solucion.asignaciones:
            self.mostrar_mensaje_inicial_grilla()
            return

        # obtener dias sin repetir
        dias = []
        if self.franjas:
            for f in self.franjas:
                if f.dia not in dias:
                    dias.append(f.dia)
        else:
            for asig in nodo_solucion.asignaciones:
                if asig.franja.dia not in dias:
                    dias.append(asig.franja.dia)

        # obtener horas sin repetir
        horas = []
        if self.franjas:
            for f in self.franjas:
                if f.hora not in horas:
                    horas.append(f.hora)
        else:
            for asig in nodo_solucion.asignaciones:
                if asig.franja.hora not in horas:
                    horas.append(asig.franja.hora)

        self.marco_tabla.columnconfigure(0, minsize=110)
        for c in range(1, len(dias) + 1):
            self.marco_tabla.columnconfigure(c, minsize=190, weight=1)

        # celda de esquina
        lbl_esquina = tk.Label(
            self.marco_tabla,
            text="BLOQUE / DIA",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=8
        )
        lbl_esquina.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        # encabezados de dias
        for c_idx, dia in enumerate(dias, start=1):
            lbl_dia = tk.Label(
                self.marco_tabla,
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

        # filas de horas y celdas
        for r_idx, hora in enumerate(horas, start=1):
            lbl_hora = tk.Label(
                self.marco_tabla,
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
                clases = [
                    asig for asig in nodo_solucion.asignaciones
                    if asig.franja.dia == dia and asig.franja.hora == hora
                ]

                if clases:
                    celda = tk.Frame(
                        self.marco_tabla,
                        bg="#DBEAFE",
                        highlightbackground="#93C5FD",
                        highlightthickness=1,
                        padx=6,
                        pady=6
                    )
                    celda.grid(row=r_idx, column=c_idx, sticky="nsew", padx=2, pady=2)

                    for i, asig in enumerate(clases):
                        if i > 0:
                            sep = tk.Frame(celda, bg="#BFDBFE", height=1)
                            sep.pack(fill="x", pady=4)

                        lbl_mat = tk.Label(
                            celda,
                            text=f"📚 {asig.curso.nombre}",
                            font=("Segoe UI", 9, "bold"),
                            bg="#DBEAFE",
                            fg="#1E3A8A",
                            anchor="w"
                        )
                        lbl_mat.pack(fill="x", anchor="w")

                        lbl_p = tk.Label(
                            celda,
                            text=f"👨‍🏫 {asig.curso.nombre_profesor}",
                            font=("Segoe UI", 8),
                            bg="#DBEAFE",
                            fg="#1E293B",
                            anchor="w"
                        )
                        lbl_p.pack(fill="x", anchor="w")

                        lbl_det = tk.Label(
                            celda,
                            text=f"📍 {asig.salon.nombre} | 👥 {asig.curso.grupo}",
                            font=("Segoe UI", 8, "italic"),
                            bg="#DBEAFE",
                            fg="#2563EB",
                            anchor="w"
                        )
                        lbl_det.pack(fill="x", anchor="w")
                else:
                    celda_vacia = tk.Frame(
                        self.marco_tabla,
                        bg="#F8FAFC",
                        highlightbackground="#E2E8F0",
                        highlightthickness=1,
                        padx=6,
                        pady=12
                    )
                    celda_vacia.grid(row=r_idx, column=c_idx, sticky="nsew", padx=2, pady=2)

                    lbl_v = tk.Label(
                        celda_vacia,
                        text="---",
                        font=("Segoe UI", 9),
                        bg="#F8FAFC",
                        fg="#94A3B8"
                    )
                    lbl_v.pack(expand=True)

        self._ajustar_scroll_grilla()

    # panel 4: tabla de metricas
    def crear_panel_estadisticas(self):
        self.labelframe_stats = ttk.LabelFrame(
            self.contenedor,
            text="  4. Estadisticas Comparativas de Rendimiento  ",
            style="Card.TLabelframe"
        )
        self.labelframe_stats.pack(fill="x", padx=20, pady=(0, 25))

        marco = tk.Frame(self.labelframe_stats, bg="#FFFFFF", padx=15, pady=8)
        marco.pack(fill="x", expand=True)

        columnas = ("algoritmo", "nodos", "tiempo", "costo", "solucion")
        self.tabla_stats = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings",
            height=4,
            style="Treeview"
        )

        self.tabla_stats.heading("algoritmo", text="Algoritmo de Busqueda", anchor="w")
        self.tabla_stats.heading("nodos", text="Nodos Explorados", anchor="center")
        self.tabla_stats.heading("tiempo", text="Tiempo (s)", anchor="center")
        self.tabla_stats.heading("costo", text="Costo Total g(n)", anchor="center")
        self.tabla_stats.heading("solucion", text="¿Solucion Encontrada?", anchor="center")

        self.tabla_stats.column("algoritmo", width=280, anchor="w")
        self.tabla_stats.column("nodos", width=160, anchor="center")
        self.tabla_stats.column("tiempo", width=150, anchor="center")
        self.tabla_stats.column("costo", width=140, anchor="center")
        self.tabla_stats.column("solucion", width=160, anchor="center")

        self.tabla_stats.pack(fill="x", expand=True)

        self.algoritmos_lista = [
            ("BFS", "Busqueda en Amplitud (BFS)"),
            ("UCS", "Busqueda de Costo Uniforme (UCS)"),
            ("IDDFS", "Profundidad Iterativa (IDDFS)"),
            ("A*", "A* (Informado)")
        ]

        for aid, nombre in self.algoritmos_lista:
            self.tabla_stats.insert(
                "",
                "end",
                iid=aid,
                values=(nombre, "---", "---", "---", "⚪ Sin ejecutar")
            )

    # actualiza la fila del algoritmo en la tabla
    def actualizar_estadistica(self, nombre_algo, resultado):
        nombre_completo = {
            "BFS": "Busqueda en Amplitud (BFS)",
            "UCS": "Busqueda de Costo Uniforme (UCS)",
            "IDDFS": "Profundidad Iterativa (IDDFS)",
            "A*": "A* (Informado)"
        }.get(nombre_algo, nombre_algo)

        nodos_str = f"{resultado.nodos_explorados:,}"
        tiempo_str = f"{resultado.tiempo_segundos:.6f} s"

        if resultado.encontro_solucion:
            solucion_str = "✔ Si (Optima)" if resultado.nodo_solucion.costo_g <= 4 else "✔ Si"
            costo_str = str(resultado.nodo_solucion.costo_g)
        else:
            solucion_str = "✖ No"
            costo_str = "N/A"

        valores = (nombre_completo, nodos_str, tiempo_str, costo_str, solucion_str)

        if self.tabla_stats.exists(nombre_algo):
            self.tabla_stats.item(nombre_algo, values=valores)
        else:
            self.tabla_stats.insert("", "end", iid=nombre_algo, values=valores)

    # ejecuta el algoritmo seleccionado
    def ejecutar_busqueda(self):
        if not (self.profesores and self.cursos and self.salones and self.franjas):
            faltantes = []
            if not self.profesores: faltantes.append("Profesores")
            if not self.cursos: faltantes.append("Cursos")
            if not self.salones: faltantes.append("Salones")
            if not self.franjas: faltantes.append("Franjas")

            messagebox.showwarning(
                "Archivos Faltantes",
                "Debe cargar los 4 archivos antes de generar el horario.\n\nFaltan por cargar:\n• " +
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
            messagebox.showerror("Error", "Algoritmo seleccionado no valido.")
            return

        nombre_corto, funcion = mapa_algoritmos[seleccion]

        self.lbl_estado_busqueda.configure(
            text=f"⏳ Ejecutando {nombre_corto}...",
            fg="#2563EB"
        )
        self.update_idletasks()

        problema = ProblemaHorario(
            cursos=self.cursos,
            profesores=self.profesores,
            salones=self.salones,
            franjas=self.franjas,
            max_consecutivas=2
        )

        resultado = funcion(problema)
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
                text=f"✖ {nombre_corto} no encontro solucion valida ({resultado.tiempo_segundos:.4f}s).",
                fg="#DC2626"
            )
            self.actualizar_estadistica(nombre_corto, resultado)
            messagebox.showinfo(
                "Sin Solucion",
                "El algoritmo no pudo encontrar una asignacion que satisfaga todas las restricciones duras."
            )

    # ejecuta los 4 algoritmos secuencialmente
    def comparar_todos(self):
        if not (self.profesores and self.cursos and self.salones and self.franjas):
            messagebox.showwarning(
                "Archivos Faltantes",
                "Debe cargar los 4 archivos de entrada para realizar la comparativa."
            )
            return

        algoritmos = [
            ("BFS", busqueda_amplitud),
            ("UCS", busqueda_costo_uniforme),
            ("IDDFS", busqueda_profundidad_iterativa),
            ("A*", busqueda_a_prima)
        ]

        mejor_solucion = None
        mejor_costo = float("inf")

        for nombre_corto, funcion in algoritmos:
            problema = ProblemaHorario(
                cursos=self.cursos,
                profesores=self.profesores,
                salones=self.salones,
                franjas=self.franjas,
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
                text=f"✔ Comparativa finalizada. Mostrando mejor solucion (Costo: {mejor_costo}).",
                fg="#16A34A"
            )

    # dibuja la grilla con la solucion
    def actualizar_horario(self, nodo_solucion):
        self.dibujar_grilla_horario(nodo_solucion)

    # abre el explorador para seleccionar un archivo
    def examinar_archivo(self, clave):
        ruta = filedialog.askopenfilename(
            title=f"Seleccionar archivo de {clave}",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            self.procesar_archivo(clave, ruta)

    # procesa y valida el archivo seleccionado
    def procesar_archivo(self, clave, ruta):
        info = self.archivos[clave]
        info["ruta_var"].set(ruta)

        try:
            funcion = info["funcion"]
            datos = funcion(ruta)

            if datos and len(datos) > 0:
                if clave == "profesores":
                    self.profesores = datos
                    tipo = "profesores"
                elif clave == "cursos":
                    self.cursos = datos
                    tipo = "cursos"
                elif clave == "salones":
                    self.salones = datos
                    tipo = "salones"
                elif clave == "franjas":
                    self.franjas = datos
                    tipo = "franjas"

                info["estado_var"].set(f"✔ Leido correctamente ({len(datos)} {tipo})")
                if info["lbl_estado"]:
                    info["lbl_estado"].configure(fg="#16A34A")
            else:
                info["estado_var"].set("✖ Archivo vacio (0 registros)")
                if info["lbl_estado"]:
                    info["lbl_estado"].configure(fg="#DC2626")

        except Exception as e:
            info["estado_var"].set("✖ Error de formato")
            if info["lbl_estado"]:
                info["lbl_estado"].configure(fg="#DC2626")
            messagebox.showerror(
                "Error de Carga",
                f"No se pudo procesar el archivo '{os.path.basename(ruta)}':\n{e}"
            )

    # autocarga de conveniencia para la carpeta datos
    def autocargar_archivos_prueba(self):
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


if __name__ == "__main__":
    app = AplicacionHorarios()
    app.mainloop()
