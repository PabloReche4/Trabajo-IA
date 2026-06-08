# Senku con planificación automática

Trabajo de la asignatura **Inteligencia Artificial** del Grado en
Ingeniería Informática — Ingeniería del Software (Universidad de
Sevilla, curso 2025/2026). Convocatoria de **junio**.

Autores: Pablo Reche Gabaldón y Sol Villegas Charlo.

El sistema resuelve el juego del Senku como un problema de planificación
clásica codificado en PDDL. Cubre la parte común con búsqueda en
anchura, y la ampliación de junio con **beam search** guiado por la
**función pagoda** (y por una heurística de **conectividad**, que es la
que acaba resolviendo los tableros más densos). Acepta como entrada un
par arbitrario de ficheros `.pddl` (dominio + problema) y devuelve la
secuencia de movimientos.

## Estructura del repositorio

```
senku/
├── pddl/
│   ├── dominio_senku.pddl              # Dominio común del Senku
│   └── problemas/                       # Un fichero por variante
│       ├── variante_1.pddl              # Octógono (37 casillas)
│       ├── variante_2.pddl              # Cruz griega grande (45)
│       ├── variante_3.pddl              # Cruz asimétrica (39)
│       ├── variante_4.pddl              # Cruz inglesa clásica (33)
│       └── variante_5.pddl              # Rombo / diamante (41)
├── src/
│   ├── tableros.py                     # Las 5 variantes (Figura 3)
│   ├── estado.py                       # ProblemaSenku + modo relajado
│   ├── heuristicas.py                  # Pagoda, conectividad, compuesta
│   ├── busqueda.py                     # BFS, DFS, Beam Search (3 variantes)
│   ├── dominio_up.py                   # PDDL vía unified_planning
│   ├── generador_pddl.py               # Tablero → fichero .pddl
│   ├── lector_pddl.py                  # PDDL → ProblemaSenku
│   ├── planificador.py                 # Wrapper sobre Fast Downward
│   ├── parche_fd.py                    # Fix UnicodeDecodeError en Windows
│   └── cli.py                          # Interfaz de línea de comandos
├── notebooks/
│   └── 01_experimentacion.ipynb        # Comparativa y estudio de huecos
├── memoria/
│   ├── memoria.tex                     # Memoria IEEE (LaTeX)
│   ├── memoria.pdf                     # PDF generado
│   ├── memoria.md                      # Versión Markdown (referencia)
│   ├── presentacion.md                 # Guion de la defensa
│   ├── IEEEtran.cls                    # Plantilla del profesor
│   └── README.md                       # Cómo compilar la memoria
├── resultados/                          # CSVs de los experimentos
├── scripts/                             # Scripts reproducibles
├── tests/                               # 19 tests unitarios
├── ENTREGA.md                          # Guía de qué subir a EV
└── README.md                           # Este fichero
```

## Variantes implementadas

Las cinco son las que aparecen en la Figura 3 del enunciado. Las 1, 3 y 5
son las obligatorias; la 2 y la 4 las dejamos como material adicional
(la cruz inglesa, V4, es el Senku clásico de la literatura).

| #  | Nombre                          | Caja  | Casillas | Obligatoria |
|----|---------------------------------|-------|---------:|-------------|
| 1  | Octógono                        | 7×7   |       37 | sí          |
| 2  | Cruz griega grande              | 9×9   |       45 | —           |
| 3  | Cruz asimétrica                 | 8×8   |       39 | sí          |
| 4  | Cruz griega clásica (inglesa)   | 7×7   |       33 | —           |
| 5  | Rombo / diamante                | 9×9   |       41 | sí          |

## Requisitos

- Python 3.10 o superior.
- `unified-planning` y `up-fast-downward` para el backend principal y la
  línea de base con Fast Downward. Si no están instalados, el sistema
  cae sobre un parser PDDL propio (solo para el dominio Senku).
- `pandas` para las tablas del notebook.

Instalación rápida:

```powershell
python -m pip install unified-planning up-fast-downward pandas
```

## Uso

### Generar los ficheros PDDL de las cinco variantes

```powershell
python -m senku.src.cli generar --destino senku/pddl/problemas
```

### Resolver un problema (dominio + instancia)

```powershell
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_3.pddl `
    --algoritmo beam-iter --intentos 4 --relajado
```

Opciones principales:

| Opción            | Descripción                                          |
|-------------------|------------------------------------------------------|
| `--algoritmo`     | `beam` (por defecto), `beam-iter`, `bfs`, `fd`       |
| `--heuristica`    | `conectividad` (recomendada) o `pagoda`              |
| `--beta`          | Anchura del haz β. Por defecto 100.                  |
| `--intentos`      | Reinicios estocásticos para beam. Por defecto 3.     |
| `--pagoda`        | `clasica` (por defecto) o `uniforme`                 |
| `--relajado`      | Meta = una pieza en cualquier sitio                  |
| `--limite`        | Cota de nodos / iteraciones                          |
| `--sin-visitados` | Desactiva la memoria global de estados visitados     |
| `--backend`       | `auto`, `unified_planning` o `ligero`                |

### Ejecutar el notebook de experimentación

```powershell
jupyter notebook senku/notebooks/01_experimentacion.ipynb
```

### Ejecutar los tests

```powershell
python senku/tests/run_tests.py
```

(O con pytest: `python -m pytest senku/tests/`)

## Notas sobre los algoritmos

- **BFS**: completa pero impráctica más allá de unas decenas de casillas
  sin cota de nodos.
- **Beam Search**: incompleto pero escalable. Su éxito depende mucho de
  la heurística y de la anchura β.
- **Función pagoda**: heurística admisible. Útil como cota inferior y
  para detectar irresolubilidad, pero **no basta** como guía de
  búsqueda en la cruz inglesa: ni siquiera con β=2000 encuentra plan.
- **Heurística de conectividad**: ordena por número de componentes
  conexas de piezas. No es admisible, pero es la que resuelve las tres
  variantes obligatorias con beam search.
- **Heurística compuesta**: pagoda + aislamiento + compacidad. Útil
  como alternativa, aunque la de conectividad rinde mejor en práctica.

Los detalles formales están en `memoria/memoria.pdf` (versión IEEE).
Para una explicación más larga y narrada, ver `DOCUMENTO_EXPLICATIVO.md`.
