# Guía de entrega — Convocatoria de junio 2026

**Asignatura:** Inteligencia Artificial — Grado en Ingeniería Informática (Ingeniería del Software).
**Autores:** Pablo Reche Gabaldón y Sol Villegas Charlo.

Este fichero recoge **qué hay que subir a la Enseñanza Virtual** y los
comandos para verificar que todo está bien justo antes de comprimir y
subir.

---

## 1. Estructura del paquete a entregar

Comprime la carpeta `senku/` entera respetando el árbol. Como mínimo el
paquete debe contener:

```
senku/
├── pddl/
│   ├── dominio_senku.pddl              # Dominio común
│   └── problemas/
│       ├── variante_1.pddl             # Octógono (37 casillas) — obligatoria
│       ├── variante_2.pddl             # Cruz griega grande (45 cas.)
│       ├── variante_3.pddl             # Cruz asimétrica (39 cas.) — obligatoria
│       ├── variante_4.pddl             # Cruz inglesa clásica (33 cas.)
│       ├── variante_5.pddl             # Rombo (41 cas.) — obligatoria
│       ├── variante_1_hueco_0_2.pddl   # Variantes con hueco alternativo
│       └── variante_5_hueco_4_2.pddl
│
├── src/                                 # Código fuente Python
│   ├── tableros.py                     # Las 5 variantes (Figura 3)
│   ├── estado.py                       # ProblemaSenku + modo relajado
│   ├── heuristicas.py                  # pagoda, conectividad, compuesta
│   ├── busqueda.py                     # BFS, DFS, Beam Search, iterativo
│   ├── dominio_up.py                   # PDDL vía unified_planning (Práctica 4)
│   ├── generador_pddl.py               # Tablero → fichero .pddl
│   ├── lector_pddl.py                  # PDDL → ProblemaSenku
│   ├── planificador.py                 # Wrapper Fast Downward
│   ├── parche_fd.py                    # Fix UnicodeDecodeError en Windows
│   └── cli.py                          # Interfaz línea de comandos
│
├── tests/
│   ├── test_basico.py                  # 19 tests
│   └── run_tests.py                    # Lanzador independiente
│
├── scripts/                             # Experimentos reproducibles
│   ├── estudio_huecos.py
│   ├── experimento_completo.py
│   ├── experimento_huecos_completo.py
│   ├── experimento_fast_downward.py
│   ├── experimento_fd_individual.py
│   ├── experimento_fd_configs.py
│   └── experimento_fd_huecos_alternativos.py
│
├── resultados/                          # CSVs de los experimentos
│   ├── huecos_completo.csv             # Barrido exhaustivo de huecos
│   ├── huecos_resumen.csv              # V1:6/13, V3:10/10, V5:3/15
│   ├── beam_conectividad.csv
│   ├── fast_downward.csv               # FD: V3 8s, V4 18s; V1,V2,V5 timeout
│   ├── fd_huecos_alternativos.csv
│   └── experimentos.csv
│
├── notebooks/
│   └── 01_experimentacion.ipynb        # Ejecutado, con salidas guardadas
│
├── memoria/
│   ├── memoria.tex                     # Fuente LaTeX (IEEE)
│   ├── memoria.pdf                     # ★ COMPILAR ANTES DE ENTREGAR
│   ├── memoria.md                      # Versión Markdown (referencia)
│   ├── presentacion.md                 # Guion de defensa
│   ├── IEEEtran.cls                    # Plantilla del profesor
│   ├── ejemplo.jpg                     # Imagen ejemplo plantilla
│   └── README.md                       # Cómo compilar (Overleaf, MiKTeX, ...)
│
├── README.md                           # Resumen del proyecto
├── DOCUMENTO_EXPLICATIVO.md            # Explicación amplia
└── ENTREGA.md                          # Este fichero
```

---

## 2. Compilación de la memoria

> **Importante:** La `memoria.pdf` que aparece en el repo **debe
> regenerarse** cada vez que se toca `memoria.tex`. Compílala otra vez
> justo antes de empaquetar.

### Opción A — PowerShell con MiKTeX o TeX Live ya instalado

```powershell
cd "c:\Users\betis\Desktop\trabajo IA\Trabajo-IA\senku\memoria"
pdflatex memoria.tex
pdflatex memoria.tex   # segunda pasada para resolver referencias
```

Si la primera vez se queja por paquetes que faltan (`pseudo`,
`booktabs`, `cite`...), MiKTeX los descarga automáticamente; basta con
aceptar el cuadro de diálogo.

Para ver el PDF resultante:

```powershell
start memoria.pdf
```

### Opción B — VSCode + extensión LaTeX Workshop

1. Instalar la extensión **LaTeX Workshop** en VSCode.
2. Abrir `senku/memoria/memoria.tex`.
3. Pulsar el icono de "build" (flecha verde, arriba-derecha) o `Ctrl+Alt+B`.
4. El PDF se genera al lado y se actualiza solo con cada guardado.

### Opción C — Overleaf (sin instalar nada)

1. Crear cuenta gratuita en <https://www.overleaf.com>.
2. *New Project → Upload Project*.
3. Subir un zip con `senku/memoria/` entera (al menos `memoria.tex`,
   `IEEEtran.cls` y `ejemplo.jpg`).
4. Marcar `memoria.tex` como *Main document*.
5. Pulsar *Recompile*.
6. *Download PDF* para descargar el fichero final.

(Ver `senku/memoria/README.md` para más detalle.)

---

## 3. Verificación antes de subir

Desde la raíz del proyecto (`Trabajo-IA/`):

```powershell
# 1. Los 19 tests deben pasar
python senku/tests/run_tests.py

# 2. Generar los PDDL de las cinco variantes (sobrescribe los existentes)
python -m senku.src.cli generar --destino senku/pddl/problemas

# 3. Resolver una variante obligatoria como smoke test
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_3.pddl `
    --algoritmo beam-iter --intentos 2 --relajado

# 4. Recompilar la memoria (ver sección 2)
```

Para el **notebook**, abrirlo en VSCode o Jupyter y ejecutar
*Kernel → Restart & Run All*. Guardar tras la ejecución para que las
salidas queden persistidas en el `.ipynb` que se entrega.

---

## 4. Checklist final

- [ ] `memoria.pdf` recompilado de la última versión de `memoria.tex`.
- [ ] Notebook ejecutado de principio a fin sin errores y guardado con sus salidas.
- [ ] `python senku/tests/run_tests.py` → 19/19 OK.
- [ ] Carpeta `senku/` empaquetada en `.zip` con la estructura de la sección 1.
- [ ] El zip incluye `memoria.pdf` (no solo el `.tex`).
- [ ] CSVs de `resultados/` presentes para el tribunal.

---

## 5. Demostración rápida en la defensa

```powershell
# Resolver la variante 3 (cruz asimétrica, obligatoria)
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_3.pddl `
    --algoritmo beam-iter --intentos 4 --relajado
```

Salida esperada: plan de 37 movimientos en pocos segundos.
