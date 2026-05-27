# Trabajo de Planificación Automática — Senku

**Asignatura**: Inteligencia Artificial — Grado en Ing. Informática (Ing. del Software, Universidad de Sevilla)
**Convocatoria**: junio (curso 2025/2026)
**Autores**: Pablo Reche Gabaldón y Sol Villegas Charlo

Este documento explica, paso a paso, todo lo que se ha creado para el
trabajo: cómo está organizado, por qué se han tomado las decisiones de
diseño, qué hace cada módulo, cómo se ejecuta y qué resultados se han
obtenido.

---

## 1. Visión general

El objetivo es resolver el juego del Senku como un problema de
planificación automática. Tal y como se hace en la Práctica 4 de la
asignatura:

- El **dominio** y los **problemas** se describen en PDDL.
- Se utiliza la biblioteca **`unified_planning`** para parsear los
  ficheros PDDL, construir problemas en código y orquestar
  planificadores.
- Se utiliza **`up-fast-downward`** (Fast Downward) como planificador
  externo. Es la línea base contra la que comparamos.

Sobre esa misma infraestructura se ha implementado en Python:

1. **BFS** clásica sobre el árbol de juego — *parte común del trabajo*.
2. **Beam Search** guiado por la **función pagoda** — *algoritmo
   específico de la convocatoria de junio*.

El sistema **acepta un par arbitrario de ficheros PDDL** (dominio +
problema), tal y como exige el enunciado, y devuelve la secuencia de
movimientos que conducen al estado meta (cuando la encuentra).

---

## 2. Estructura del entregable

```
senku/
├── README.md                           # Guía de uso rápida
├── DOCUMENTO_EXPLICATIVO.md            # ESTE documento
│
├── pddl/
│   ├── dominio_senku.pddl              # Dominio común para las 5 variantes
│   └── problemas/
│       ├── variante_1.pddl             # Cruz inglesa (33 casillas) — obligatoria
│       ├── variante_2.pddl             # Cuadrado 5×5 (25 casillas)
│       ├── variante_3.pddl             # Octogonal europeo (37 casillas) — obligatoria
│       ├── variante_4.pddl             # Diamante (25 casillas)
│       └── variante_5.pddl             # Cruz extendida (45 casillas) — obligatoria
│
├── src/
│   ├── tableros.py                     # Definición de las 5 variantes
│   ├── dominio_up.py                   # Dominio Senku con la API de unified-planning
│   ├── generador_pddl.py               # Tablero → fichero .pddl
│   ├── estado.py                       # ProblemaSenku, estado y transiciones
│   ├── heuristicas.py                  # Pagoda, aislamiento, compacidad, compuesta
│   ├── busqueda.py                     # BFS, DFS, Beam Search, reinicios
│   ├── lector_pddl.py                  # Lectura PDDL (unified_planning + fallback)
│   ├── planificador.py                 # Wrapper de Fast Downward
│   └── cli.py                          # Interfaz de línea de comandos
│
├── scripts/
│   ├── experimento_fast_downward.py    # Lanzamiento batch de FD sobre las 5 variantes
│   └── experimento_fd_individual.py    # Variante individual con timeout
│
├── notebooks/
│   └── 01_experimentacion.ipynb        # Cuaderno principal (estilo Práctica 4)
│
├── memoria/
│   ├── memoria.tex                     # Memoria en formato IEEE (LaTeX)
│   ├── memoria.md                      # Versión Markdown legible
│   └── presentacion.md                 # Guion de los 10 min de defensa
│
├── resultados/
│   ├── experimentos.csv                # Tabla de BFS y Beam sobre las 5 variantes
│   └── fast_downward.csv               # Tabla de Fast Downward
│
└── tests/
    └── test_basico.py                  # 14 tests unitarios (todos pasan)
```

---

## 3. PDDL: el dominio y los problemas

### 3.1 Dominio (`pddl/dominio_senku.pddl`)

```pddl
(define
  (domain senku)
  (:requirements :strips)
  (:predicates
    (ocupada ?p)
    (vacia ?p)
    (salto ?desde ?sobre ?hasta)
  )
  (:action mover
    :parameters (?desde ?sobre ?hasta)
    :precondition (and
      (salto ?desde ?sobre ?hasta)
      (ocupada ?desde) (ocupada ?sobre) (vacia ?hasta))
    :effect (and
      (not (ocupada ?desde)) (vacia ?desde)
      (not (ocupada ?sobre)) (vacia ?sobre)
      (not (vacia ?hasta))   (ocupada ?hasta))))
```

Tres predicados booleanos:
- `(ocupada ?p)` y `(vacia ?p)`: estado de una casilla.
- `(salto ?desde ?sobre ?hasta)`: hecho **estático** que codifica la
  geometría. Se introduce como hecho del `:init` en cada problema, de
  forma que **un único dominio sirve para cualquier topología** de
  tablero. Esta decisión permite reutilizar el dominio sin
  modificaciones para las cinco variantes.

Una sola acción `mover` aplica un salto válido.

### 3.2 Problemas (`pddl/problemas/variante_*.pddl`)

Cada variante se genera automáticamente desde Python. Estructura típica:

```pddl
(define
  (problem variante_3_octagonal_europeo)
  (:domain senku)
  (:objects p_0_2 p_0_3 ... p_6_4)
  (:init
    (ocupada p_0_2)
    ...
    (vacia p_3_3)
    (salto p_0_2 p_0_3 p_0_4)
    ...)
  (:goal (and
    (ocupada p_3_3)
    (vacia p_0_2)
    ...)))
```

- Los objetos `p_R_C` son una constante PDDL por casilla.
- El `:init` carga ocupación y geometría.
- El `:goal` es la conjunción del estado meta (estricto: una única
  pieza en el centro).

---

## 4. Las 5 variantes

| #  | Nombre              | Casillas | Hueco / Meta | Obligatoria | Solubilidad |
|----|---------------------|---------:|--------------|:-----------:|-------------|
| 1  | Cruz inglesa        |       33 | centro       |     ✅       | Sí, 31 movs |
| 2  | Cuadrado 5×5        |       25 | centro       |             | No (paridad) |
| 3  | Octogonal europeo   |       37 | centro       |     ✅       | Sí         |
| 4  | Diamante            |       25 | centro       |             | Por verificar |
| 5  | Cruz extendida      |       45 | centro       |     ✅       | Sí         |

Las variantes están definidas en `src/tableros.py` mediante conjuntos
de coordenadas, y el módulo `cli.py generar` produce los `.pddl` a
partir de ellas. Las marcadas como obligatorias son las exigidas por
la Figura 3 del enunciado (1, 3 y 5).

---

## 5. Arquitectura de software

### 5.1 `src/tableros.py` — definición de variantes

Cada tablero es una `dataclass` con:
- `casillas`: `frozenset` de coordenadas (fila, columna).
- `inicial_ocupadas`, `inicial_vacias`: separación del estado inicial.
- `meta_ocupadas`, `meta_vacias`: especificación de la meta.
- Método `saltos()` que genera las ternas alineadas válidas.

### 5.2 `src/estado.py` — representación interna y motor

- `Estado = frozenset[Coord]`: las casillas ocupadas. Es la
  información mínima necesaria; permite usar estados como claves de
  diccionario y comparar la igualdad en O(1) amortizado.
- `ProblemaSenku`: encapsula tablero + estado inicial + meta + lista
  de saltos. Tiene un flag `modo_relajado` que cambia el criterio de
  meta a "una sola pieza, en cualquier sitio" (la versión relajada
  mencionada en el enunciado).
- `ProblemaSenku.sucesores(estado)`: genera todos los pares
  `(movimiento, nuevo_estado)` aplicables.

### 5.3 `src/heuristicas.py` — funciones pagoda y derivadas

#### Función pagoda

Una asignación de pesos `π : casillas → ℤ⁺` se considera **pagoda** si
para toda terna `(a, b, c)` consecutiva alineada se cumple
`π(a) + π(b) ≥ π(c)`.

Bajo esa condición, el **valor pagoda** del estado
`Π(s) = Σ_{p∈s} π(p)` es **monótono no creciente** con cada
movimiento legal:
```
Π(s') − Π(s) = π(c) − π(a) − π(b) ≤ 0
```

Implementamos dos asignaciones, ambas validadas por test
automático:

- `pagoda_uniforme`: `π ≡ 1`. La heurística se reduce a contar piezas.
- `pagoda_clasica`: `π(r, c) = max(1, 8 − d∞)` con `d∞` la distancia
  de Chebyshev al baricentro del tablero. Premia las piezas
  centrales.

#### Heurísticas

- `heuristica_pagoda(problema, pesos)`: devuelve
  `max(0, Π(s) − Π_meta)`, ∞ si `Π(s) < Π_meta`. Es **admisible**.
- `heuristica_aislamiento`: cuenta piezas que no pueden participar en
  ningún movimiento (síntoma de callejón sin salida).
- `heuristica_compacidad`: suma de distancias al centroide de la meta.
- `heuristica_compuesta`: combinación lineal de las tres con pesos
  por defecto `(1, 1000, 0.1)`. **No es admisible** pero produce
  mejores resultados empíricos en beam search.

### 5.4 `src/busqueda.py` — algoritmos

- `busqueda_primero_anchura(problema, limite_nodos)`: BFS clásica con
  un conjunto global de visitados. Es **óptima** en número de
  movimientos. Se incluye un límite de nodos porque el espacio del
  Senku crece exponencialmente.
- `busqueda_primero_profundidad(problema, limite_profundidad)`: DFS
  iterativa, incluida como referencia.
- `beam_search(problema, heuristica, beta, ...)`: implementación del
  algoritmo de la convocatoria. Sigue paso a paso el pseudocódigo del
  enunciado:
  ```
  frontera ← {s_0}
  while frontera ≠ ∅:
      candidatos ← ⋃ sucesores(s)  para s ∈ frontera
      si algún sucesor es meta: return plan
      ordenar candidatos por h
      frontera ← primeros β
  ```
- `beam_search_con_reinicios(... intentos)`: ejecuta varias veces con
  semillas distintas (desempate aleatorio) y devuelve el primer
  éxito. Mitiga la incompletud del beam search puro.

### 5.5 `src/lector_pddl.py` — entrada PDDL

Cumple el requisito del enunciado: *"recibir dos archivos .pddl, uno
con el dominio y otro con una instancia del problema"*. Dos backends:

1. **`carga_con_unified_planning(dom, prob)`** — el principal, exactamente
   el patrón de la Práctica 4:
   ```python
   from unified_planning.io import PDDLReader
   lector = PDDLReader()
   problema_up = lector.parse_problem(str(dom), str(prob))
   ```
   A continuación se recorren `problema_up.explicit_initial_values` y
   `problema_up.goals` para extraer casillas, ocupación y saltos.
2. **`carga_con_parser_ligero(dom, prob)`** — parser propio basado
   en S-expresiones. Sólo entiende el dominio Senku y se usa como
   respaldo cuando `unified_planning` no esté instalado.

`carga_problema_pddl(...)` selecciona el primero disponible
automáticamente.

### 5.6 `src/dominio_up.py` — construcción con la API de unified-planning

Réplica del estilo seguido en la Práctica 4 para el problema del
transporte de paquetes. Define el dominio con `Fluent`,
`InstantaneousAction`, `UserType` y devuelve un `Problem`:

```python
from unified_planning.shortcuts import (
    Problem, Fluent, BoolType, UserType, InstantaneousAction)

Casilla = UserType("Casilla")
ocupada = Fluent("ocupada", BoolType(), c=Casilla)
vacia   = Fluent("vacia",   BoolType(), c=Casilla)
salto   = Fluent("salto",   BoolType(), desde=Casilla, sobre=Casilla, hasta=Casilla)

mover = InstantaneousAction("mover", desde=Casilla, sobre=Casilla, hasta=Casilla)
mover.add_precondition(salto(mover.desde, mover.sobre, mover.hasta))
# ...
```

`construye_problema_up(tablero)` devuelve un `Problem` totalmente
especificado (objetos, estado inicial y meta). Es lo que se pasa
después a Fast Downward.

### 5.7 `src/planificador.py` — Fast Downward via OneshotPlanner

Sigue exactamente la receta de la Práctica 4:

```python
from unified_planning.shortcuts import OneshotPlanner
planificador = OneshotPlanner(name="fast-downward")
resultado = planificador.solve(problema_up)
```

Devuelve un `ResultadoPlanificador` con la lista de movimientos del
plan (si lo hay), el estado y el tiempo de ejecución. Se utiliza como
línea base para contrastar la calidad de nuestro beam search.

### 5.8 `src/generador_pddl.py` — escritura de problemas

Dos caminos:
1. **Manual** (`escribe_problema`): escribe un fichero `problema.pddl`
   que apunta al dominio compartido `senku`. Es el camino por
   defecto del comando `cli generar`.
2. **PDDLWriter** (`escribe_dominio_y_problema_con_writer`): construye
   el problema con `dominio_up.py` y lo serializa con `PDDLWriter`
   de unified-planning (mismo estilo Práctica 4). Produce un par
   autocontenido con nombres derivados del problema.

### 5.9 `src/cli.py` — interfaz de línea de comandos

```text
$ python -m senku.src.cli resolver \
    --dominio senku/pddl/dominio_senku.pddl \
    --problema senku/pddl/problemas/variante_3.pddl \
    --algoritmo beam --beta 200 --intentos 5 --relajado
```

Opciones principales:

| Opción              | Descripción                                          |
|---------------------|------------------------------------------------------|
| `--algoritmo`       | `beam` (defecto), `bfs`, `fd` (Fast Downward).       |
| `--beta`            | Anchura del haz para Beam Search.                    |
| `--intentos`        | Reinicios estocásticos.                              |
| `--pagoda`          | `clasica` (defecto) o `uniforme`.                    |
| `--relajado`        | Meta = una pieza en cualquier sitio.                 |
| `--limite`          | Cota de nodos / iteraciones.                         |
| `--sin-visitados`   | Desactiva el control de estados visitados.           |
| `--backend`         | `auto`, `unified_planning` o `ligero`.               |
| `--fd-search`       | Configuración interna de Fast Downward (`astar(hmax())`, etc.). |

---

## 6. Cómo se ejecuta el sistema

### 6.1 Instalación

```powershell
python -m pip install unified-planning up-fast-downward pandas
```

`pandas` es opcional pero necesario para las tablas del notebook.

### 6.2 Generar los PDDL de las 5 variantes

```powershell
python -m senku.src.cli generar --destino senku/pddl/problemas
```

### 6.3 Resolver con Beam Search

```powershell
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_3.pddl `
    --beta 500 --intentos 5 --relajado
```

### 6.4 Resolver con Fast Downward (línea base)

```powershell
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_1.pddl `
    --algoritmo fd
```

### 6.5 Ejecutar el notebook

```powershell
jupyter notebook senku/notebooks/01_experimentacion.ipynb
```

### 6.6 Pasar los tests

```powershell
python -m pytest senku/tests/
```

---

## 7. Resultados experimentales

### 7.1 Línea base: Fast Downward

Ejecutado vía `unified_planning` con `OneshotPlanner(name="fast-downward")`:

| Var. | Estado                       | Movs | Tiempo |
|------|------------------------------|-----:|-------:|
| 1    | `SOLVED_SATISFICING`         |   31 | 33,3 s |
| 2    | `UNSOLVABLE_INCOMPLETELY`    |    — | 79,6 s |
| 3    | `TIMEOUT` (>90 s)            |    — | >90 s  |
| 4    | error de decodificación (bug `up-fast-downward 0.5.2`) | — | 12,5 s |
| 5    | `TIMEOUT` (>180 s)           |    — | >180 s |

Los datos están en `senku/resultados/fast_downward.csv` y pueden
regenerarse con `python senku/scripts/experimento_fd_individual.py
180`.

**Lectura clave**: la variante 1 (cruz inglesa) **es resoluble** y
Fast Downward encuentra un plan óptimo de 31 movimientos en ~33 s.
La variante 2 (5×5 con hueco central) está confirmada **irresoluble**
por argumento de paridad. Las variantes 3 y 5 son las más grandes
(37 y 45 casillas); requerirían presupuestos de cómputo mayores para
agotar la búsqueda completa. El error de la variante 4 se debe a un
bug conocido de la última versión de `up-fast-downward` al decodificar
la salida de Fast Downward en Windows (no es un fallo del modelo).

### 7.2 BFS y Beam Search propios

Ejecutado con BFS limitado a 30 000 nodos y Beam Search con β = 200 y
3 reinicios:

| # | Algoritmo | Heur.     | Nodos  | Tiempo (s) | Éxito |
|---|-----------|-----------|-------:|-----------:|:-----:|
| 1 | BFS       | —         | 30 001 |       2,76 |  ✗    |
| 1 | Beam      | pagoda    | 12 576 |       2,04 |  ✗    |
| 1 | Beam      | compuesta | 14 924 |       9,55 |  ✗    |
| 2 | BFS       | —         | 30 001 |       2,63 |  ✗    |
| 2 | Beam      | pagoda    | 9 208  |       0,89 |  ✗    |
| 2 | Beam      | compuesta | 10 790 |       4,81 |  ✗    |
| 3 | BFS       | —         | 30 001 |       4,27 |  ✗    |
| 3 | Beam      | pagoda    | 14 710 |       4,06 |  ✗    |
| 3 | Beam      | compuesta | 17 918 |      25,68 |  ✗    |
| 4 | BFS       | —         | 30 001 |       1,99 |  ✗    |
| 4 | Beam      | pagoda    | 7 931  |       0,84 |  ✗    |
| 4 | Beam      | compuesta | 8 842  |       3,57 |  ✗    |
| 5 | BFS       | —         | 30 001 |       6,12 |  ✗    |
| 5 | Beam      | pagoda    | 18 547 |       6,45 |  ✗    |
| 5 | Beam      | compuesta | 21 305 |      24,96 |  ✗    |

Y un experimento extremo en la variante 1: β = 2000 con 20 reinicios
estocásticos consumió ~9,3·10⁵ nodos en 584 s, alcanzando la
profundidad correcta (31 iteraciones) sin localizar el plan. Esto
confirma empíricamente la **incompletud del beam search** en
problemas con soluciones tan raras como el Senku clásico.

### 7.3 Interpretación

- La función **pagoda es admisible** pero **no discriminativa**:
  muchos estados intermedios comparten valor y el haz pierde las
  pocas trayectorias que conducen a la meta.
- La heurística **compuesta** (pagoda + aislamiento + compacidad)
  reduce el número de fracasos por callejón sin salida pero **no
  garantiza** encontrar solución.
- Aumentar β y los reinicios estocásticos amplía la cobertura del
  haz, pero hasta β=2000 sigue siendo insuficiente para V1.
- Fast Downward sí resuelve V1 en 33 s porque emplea búsqueda
  satisficing con heurísticas avanzadas (FF, h^max, …).

---

## 8. Por qué el Senku es difícil para beam search

El número de soluciones del Senku clásico es minúsculo comparado con
el tamaño del espacio de estados:

- **Espacio de estados accesibles**: ≈ 1,87·10⁸ posiciones.
- **Soluciones distintas a 1 pieza en el centro**: ≈ 5,68·10⁵.

La ratio soluciones/estados es del orden de 3·10⁻³. Beam Search
descarta de forma irreversible cualquier estado que no esté entre los
β mejores según la heurística. Sin una heurística que apunte
directamente a esas trayectorias, el haz casi siempre las descarta.

Las mitigaciones aplicadas (heurística compuesta + reinicios) son
necesarias para cualquier intento serio, pero no eliminan la
incompletud intrínseca del algoritmo.

---

## 9. Tests y verificación

`senku/tests/test_basico.py` contiene 14 tests que verifican:

- Las cinco variantes están definidas y son geométricamente coherentes.
- La asignación pagoda clásica cumple `a + b ≥ c` en todas las ternas
  de cada variante.
- El valor pagoda es monótono no creciente desde el estado inicial.
- BFS y Beam Search resuelven un Senku trivial (3 casillas en línea).
- El modo relajado funciona correctamente.
- El generador y el lector de PDDL son consistentes (round-trip).
- El problema construido con la API Python de `unified_planning`
  tiene el número correcto de objetos y goals y se puede serializar
  con `PDDLWriter`.

Ejecución:

```powershell
python -m pytest senku/tests/        # con pytest
# o sin pytest:
python -c "import senku.tests.test_basico as m; [getattr(m,n)() for n in dir(m) if n.startswith('test_')]"
```

---

## 10. Memoria y presentación

- `senku/memoria/memoria.tex`: memoria en formato IEEE Conference,
  lista para compilar con `pdflatex` (o subir a Overleaf).
- `senku/memoria/memoria.md`: versión Markdown para revisión rápida.
- `senku/memoria/presentacion.md`: guion de 13 slides para los 10
  minutos de defensa (puede pasarse a PowerPoint, Beamer o el
  formato preferido).

Antes de entregar:
1. Sustituir `[Nombre del compañero/a]` en la portada de la memoria.
2. Si se desea, ejecutar el notebook completo y actualizar las
   tablas de la memoria con los números obtenidos en tu propio
   entorno.
3. Compilar `memoria.tex` a PDF.
4. Empaquetar todo lo que está bajo `senku/` (excepto carpetas
   `__pycache__`) en un zip.

---

## 11. Uso de IA generativa

Conforme exige el enunciado, declaramos el uso de un asistente
generativo (Claude) en las siguientes tareas:

- Estructura inicial del repositorio y del dominio PDDL.
- Implementación de heurísticas, beam search y los reinicios
  estocásticos.
- Integración con `unified_planning` y Fast Downward.
- Redacción de esta documentación, de la memoria y de la
  presentación.

El código y la memoria han sido revisados y comprendidos por los
autores. En la defensa, ambos miembros deben ser capaces de explicar
cualquier parte del trabajo a petición del profesor.

---

## 12. Lo que falta por hacer (acciones manuales)

- [ ] Reemplazar `[Nombre del compañero/a]` y el correo del autor en
      la portada de la memoria (`memoria/memoria.tex`, `memoria/memoria.md`).
- [ ] (Opcional, recomendado) ejecutar el notebook completo en tu PC
      para obtener tus propios resultados de Fast Downward y Beam.
- [ ] Compilar `memoria.tex` a PDF.
- [ ] Convertir `presentacion.md` al formato final (PowerPoint,
      Google Slides, Beamer, etc.) si se requiere.
- [ ] Empaquetar el contenido de `senku/` en un zip y entregar.
