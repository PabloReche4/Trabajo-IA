# Senku con planificación automática

Trabajo de la asignatura **Inteligencia Artificial** del Grado en
Ingeniería Informática — Ingeniería del Software (Universidad de
Sevilla, curso 2025/2026). Convocatoria de **junio**.

El sistema resuelve el juego del Senku como un problema de planificación
clásica codificado en PDDL. Implementa la búsqueda en anchura (parte
común) y el algoritmo **beam search** guiado por la **función pagoda**
(ampliación específica de la convocatoria de junio). Está pensado para
recibir un par arbitrario de ficheros `.pddl` (dominio + problema) y
devolver la secuencia de movimientos hasta el estado meta.

## Estructura del repositorio

```
senku/
├── pddl/
│   ├── dominio_senku.pddl              # Dominio común del Senku
│   └── problemas/                       # Generados: una variante por fichero
│       ├── variante_1.pddl              # Cruz inglesa (33 casillas)
│       ├── variante_2.pddl              # Cuadrado 5×5 (25 casillas)
│       ├── variante_3.pddl              # Octogonal europeo (37 casillas)
│       ├── variante_4.pddl              # Diamante (25 casillas)
│       └── variante_5.pddl              # Cruz extendida (45 casillas)
├── src/
│   ├── tableros.py                     # Definición de las 5 variantes
│   ├── generador_pddl.py               # Tablero → fichero .pddl
│   ├── estado.py                       # Representación de estados y ProblemaSenku
│   ├── heuristicas.py                  # Pagoda, aislamiento, compacidad, compuesta
│   ├── busqueda.py                     # BFS, DFS, Beam Search, reinicios
│   ├── lector_pddl.py                  # Lectura PDDL (unified-planning + fallback)
│   └── cli.py                          # Interfaz de línea de comandos
├── notebooks/
│   └── 01_experimentacion.ipynb        # Comparativa BFS vs Beam Search
├── memoria/
│   ├── memoria.tex                     # Memoria en formato IEEE (LaTeX)
│   └── memoria.md                      # Versión Markdown legible
├── resultados/
│   └── experimentos.csv                # Salida de los experimentos
├── tests/                              # Tests unitarios (pytest)
└── README.md                           # Este fichero
```

## Requisitos

- Python 3.10 o superior.
- (Opcional) `unified-planning` y `up-fast-downward` para usar el
  backend recomendado por la asignatura. Si no están instalados, el
  sistema cae automáticamente sobre un parser PDDL propio específico
  para el dominio Senku.
- (Opcional) `pandas` para las tablas del notebook.

Instalación rápida (recomendada):

```powershell
python -m pip install unified-planning up-fast-downward pandas
```

## Uso del sistema

### Generar los ficheros PDDL de las cinco variantes

```powershell
python -m senku.src.cli generar --destino senku/pddl/problemas
```

### Resolver un problema (dominio + problema PDDL)

```powershell
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_3.pddl `
    --beta 200 --intentos 5 --relajado
```

Opciones principales:

| Opción          | Descripción                                            |
|-----------------|--------------------------------------------------------|
| `--algoritmo`   | `beam` (por defecto) o `bfs`                           |
| `--beta`        | Anchura del haz (β). Por defecto 100.                  |
| `--intentos`    | Reinicios estocásticos (sólo con beam). Por defecto 3.  |
| `--pagoda`      | `clasica` (por defecto) o `uniforme`.                  |
| `--relajado`    | Meta = una pieza en cualquier sitio.                   |
| `--limite`      | Cota de nodos / iteraciones.                           |
| `--sin-visitados` | Desactiva la memoria global de estados visitados.    |
| `--backend`     | `auto`, `unified_planning` o `ligero`.                |

### Ejecutar el notebook de experimentación

```powershell
jupyter notebook senku/notebooks/01_experimentacion.ipynb
```

### Ejecutar los tests

```powershell
python -m pytest senku/tests/
```

## Notas sobre los algoritmos

- **BFS**: completa pero impráctica más allá de tableros de 25
  casillas sin un límite de nodos.
- **Beam Search**: incompleto pero escalable. Su rendimiento depende
  críticamente de la heurística y del valor de β.
- **Función pagoda**: heurística admisible, útil como cota inferior.
  Se proporciona en dos versiones (uniforme y clásica).
- **Heurística compuesta**: pagoda + aislamiento + compacidad. No es
  admisible pero produce mejores resultados empíricos en problemas
  donde las soluciones son escasas (como el Senku clásico).

Los detalles se explican en `memoria/memoria.md` y `memoria/memoria.tex`.
