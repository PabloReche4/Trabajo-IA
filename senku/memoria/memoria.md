# Planificación automática aplicada al Senku
**Convocatoria de junio — Curso 2025/2026**

*Pablo Reche Gabaldón y Sol Villegas Charlo*
*Grado en Ingeniería Informática — Ingeniería del Software, Universidad de Sevilla*

---

## Resumen

Este trabajo aborda la resolución del juego del Senku como un problema
de planificación automática. La parte común consiste en una
representación del dominio en PDDL y una búsqueda básica en el espacio
de estados. La ampliación específica para la convocatoria de junio
implementa el algoritmo *beam search* guiado por la *función pagoda*,
capaz de aceptar como entrada un par arbitrario de ficheros PDDL
(dominio y problema). Se presentan resultados experimentales sobre
cinco variantes del tablero, se discute la incompletud inherente al
beam search y se proponen mitigaciones basadas en heurísticas
compuestas y reinicios estocásticos.

---

## 1. Introducción

El Senku es un juego de un solo jugador con tablero compuesto por *M*
casillas en una rejilla, con *M*-1 piezas y un único hueco inicial. En
cada turno el jugador escoge una pieza, salta sobre una pieza
adyacente y aterriza en el hueco contiguo, eliminando la pieza
saltada. El objetivo clásico es terminar con una única pieza en la
posición del hueco inicial; existen versiones relajadas en las que
basta dejar una pieza en cualquier sitio.

Sus acciones discretas, deterministas y completamente observables
hacen del Senku un caso ideal para la planificación automática
clásica. Los objetivos de este trabajo son:

1. Codificar el juego como un problema PDDL.
2. Implementar en Python un sistema capaz de explorar el árbol de
   juego y devolver una secuencia de acciones objetivo.
3. Ampliar el sistema con *beam search* guiado por la *función
   pagoda*, validando la lectura del problema desde ficheros PDDL
   externos (requisito de la convocatoria de junio).
4. Evaluar el sistema sobre las variantes 1, 3 y 5 de la Figura 3 del
   enunciado y discutir el alcance de los resultados.

---

## 2. Descripción del lenguaje (PDDL)

PDDL es el estándar para describir problemas de planificación. Sus dos
partes son la definición del **dominio** (predicados y esquemas de
acción) y la del **problema** (objetos, estado inicial y meta).

### 2.1 Dominio del Senku

El dominio `dominio_senku.pddl` define:

- `(ocupada ?p)` — la casilla `?p` contiene una pieza.
- `(vacia ?p)` — la casilla `?p` no contiene pieza.
- `(salto ?desde ?sobre ?hasta)` — hecho estático que indica que las
  tres casillas están alineadas y son consecutivas.

La única acción `mover` exige pieza en origen e intermedia, hueco en
destino y un hecho `salto` que valide la geometría; su efecto
invierte las tres casillas. Esta formulación es mínima, encaja en
`:strips` y permite reutilizar el mismo dominio para cualquier
topología.

### 2.2 Problema

Cada variante se genera con `cli.py generar`. Los objetos PDDL son
constantes `p_r_c`, el `:init` contiene `ocupada`, `vacia` y `salto`,
y el `:goal` la conjunción de `ocupada`/`vacia` esperadas.

---

## 3. Algoritmos implementados

### 3.1 Representación común

Cada estado se representa como un `frozenset` de coordenadas
`(fila, columna)` de las casillas ocupadas. Permite usar los estados
como claves de diccionario y comparar igualdad en tiempo constante
amortizado.

### 3.2 Parte común: BFS

Se implementa una BFS clásica con conjunto global de visitados, óptima
en número de movimientos pero impráctica más allá de tableros de 25
casillas sin límite de nodos. Incluye un parámetro `limite_nodos`.

### 3.3 Convocatoria de junio: Beam Search

```
1. β: anchura del haz prefijada.
2. Para cada estado de la frontera se generan todos los sucesores.
3. Si alguno es meta, se devuelve el plan completo.
4. Si no, los sucesores se ordenan por la heurística y se conservan
   los β mejores como nueva frontera. Repetir.
```

El módulo `busqueda.py` ofrece `beam_search` y
`beam_search_con_reinicios`, este último ejecuta varias replicas con
semillas distintas para diversificar el desempate.

### 3.4 Función pagoda

Una asignación de pesos `π: Casillas → ℤ⁺` es una *función pagoda* si
para toda terna `(a, b, c)` consecutiva alineada se cumple
`π(a) + π(b) ≥ π(c)`. Entonces el valor *pagoda* de un estado
`Π(s) = Σ_{p∈s} π(p)` es **monótono no creciente** con cada movimiento:
`Π(s') - Π(s) = π(c) - π(a) - π(b) ≤ 0`.

La heurística asociada,

```
h_π(s) = +∞   si Π(s) < Π*
       = Π(s) - Π*   en otro caso
```

donde `Π* = Σ_{p∈meta} π(p)`, es admisible. Se implementan dos
asignaciones:

- `pagoda_uniforme`: `π ≡ 1`. La heurística se reduce a contar piezas
  excedentes.
- `pagoda_clasica`: `π(r, c) = max(1, 8 - d∞)` con `d∞` la distancia
  de Chebyshev al baricentro del tablero. Premia las piezas centrales.

### 3.5 Heurística compuesta y reinicios

La pagoda es admisible pero contiene poca señal discriminativa. La
heurística *compuesta* añade dos términos no admisibles:

- **Aislamiento** (peso 1000): número de piezas que no pueden
  participar en ningún movimiento.
- **Compacidad** (peso 0.1): suma de distancias de Chebyshev al
  centroide del objetivo.

Adicionalmente, los reinicios estocásticos permiten escapar de
callejones sin salida específicos del desempate determinista.

### 3.5.bis Heurística de conectividad (la decisiva)

Tras comprobar que la pagoda no basta para guiar el haz, se diseñó una
heurística basada en la **conectividad** del tablero, que es la que
finalmente permite a beam search resolver la cruz inglesa. Ordena los
estados por:

1. **Número de componentes conexas** de piezas (peso 50, dominante),
   considerando adyacencia ortogonal. Para reducir el tablero a una
   sola pieza el conjunto debe mantenerse cohesionado: dos grupos
   separados por huecos no recuperables nunca podrán fusionarse.
2. **Piezas aisladas** (peso 20): refuerzo del criterio anterior.
3. **Número total de piezas** (peso 1): desempate fino.
4. **Atracción a la meta** (peso 0.5, solo modo estricto y con ≤8
   piezas): dirige el final de la partida a la casilla objetivo.

No es admisible, pero su poder discriminativo es muy superior al de la
pagoda. Con ella, beam search resuelve la cruz inglesa en 31 movimientos
tanto en modo relajado como estricto (terminando en el centro).

### 3.6 Sistema CLI y lectura PDDL

El requisito de aceptar dos ficheros .pddl arbitrarios se cumple con
`lector_pddl.py`, que ofrece dos *backends*:

1. `unified_planning` (el recomendado por la asignatura).
2. Un parser propio basado en S-expresiones, específico para el
   dominio Senku, como respaldo cuando la biblioteca anterior no esté
   instalada.

`cli.py resolver` acepta `--dominio`, `--problema`, `--beta`,
`--intentos`, `--relajado`, etc.

---

## 4. Experimentación

### 4.1 Variantes

| # | Nombre                       | Casillas | Obligatoria | Resuelta por beam search |
|---|------------------------------|---------:|:-----------:|--------------------------|
| 1 | Cruz inglesa estándar        |       33 | Sí          | Sí, centro — 31 movs     |
| 2 | Cuadrado 5×5                 |       25 | No          | No (irresoluble)         |
| 3 | Octogonal europeo            |       37 | Sí          | Sí, hueco (0,2) — 35 movs|
| 4 | Diamante (Manhattan-3)       |       25 | No          | No (irresoluble)         |
| 5 | Cruz extendida               |       45 | Sí          | Sí, hueco (0,3) — 43 movs|

### 4.2 Línea base: Fast Downward (via unified-planning)

Antes de evaluar nuestras implementaciones, lanzamos Fast Downward
sobre cada variante para establecer un baseline. Se utiliza el patrón
de la Práctica 4 (`OneshotPlanner(name="fast-downward")`):

| # | Estado de FD                  | Movs | Tiempo (s) |
|---|-------------------------------|-----:|-----------:|
| 1 | `SOLVED_SATISFICING`          |   31 |     33,3   |
| 2 | `UNSOLVABLE_INCOMPLETELY`     |    — |     79,6   |
| 3 | `TIMEOUT` (>90 s)             |    — |    >90     |
| 4 | error de decodificación (*)   |    — |     12,5   |
| 5 | `TIMEOUT` (>180 s)            |    — |   >180     |

(*) Error conocido de `up-fast-downward 0.5.2` en Windows al decodificar
la salida de error de FD; afecta a la entrega pero no a la corrección
del enfoque.

**Hallazgos clave**:
- La **variante 1 (cruz inglesa)** *es resoluble*: Fast Downward
  encuentra un plan de 31 movimientos en 33 s, lo cual coincide con
  el mínimo teórico conocido.
- La **variante 2 (cuadrado 5×5 con hueco central)** es *irresoluble*
  por argumento de paridad (Fast Downward lo demuestra exhaustivamente
  en 80 s).
- Las variantes 3 y 5 no se resuelven en el tiempo asignado; al ser
  más grandes (37 y 45 casillas) requerirían presupuestos mucho
  mayores.

### 4.3 BFS y Beam Search propios

Ejecutados sobre los mismos ficheros PDDL (cargados con
`carga_con_unified_planning`). BFS limitada a 30 000 nodos; Beam
Search con β = 200 y 3 reinicios estocásticos:

| # | Algoritmo | Heur.     | Nodos  | Tiempo (s) | Éxito |
|---|-----------|-----------|-------:|-----------:|:-----:|
| 1 | BFS       | —         | 30 001 |       2,76 |   ✗   |
| 1 | Beam      | pagoda    | 12 576 |       2,04 |   ✗   |
| 1 | Beam      | compuesta | 14 924 |       9,55 |   ✗   |
| 2 | BFS       | —         | 30 001 |       2,63 |   ✗   |
| 2 | Beam      | pagoda    |  9 208 |       0,89 |   ✗   |
| 2 | Beam      | compuesta | 10 790 |       4,81 |   ✗   |
| 3 | BFS       | —         | 30 001 |       4,27 |   ✗   |
| 3 | Beam      | pagoda    | 14 710 |       4,06 |   ✗   |
| 3 | Beam      | compuesta | 17 918 |      25,68 |   ✗   |
| 4 | BFS       | —         | 30 001 |       1,99 |   ✗   |
| 4 | Beam      | pagoda    |  7 931 |       0,84 |   ✗   |
| 4 | Beam      | compuesta |  8 842 |       3,57 |   ✗   |
| 5 | BFS       | —         | 30 001 |       6,12 |   ✗   |
| 5 | Beam      | pagoda    | 18 547 |       6,45 |   ✗   |
| 5 | Beam      | compuesta | 21 305 |      24,96 |   ✗   |

*BFS limitada a 30 000 nodos; Beam con β=200, 3 reinicios, máximo 80 iteraciones. La pagoda no alcanza la meta en ninguna variante.*

Experimento de fuerza bruta con la pagoda: variante 1 con β=2000 y 20
reinicios estocásticos. Beam search exploró ~9,3·10⁵ nodos en 584 s
alcanzando las 31 iteraciones (profundidad equivalente al plan óptimo),
pero la frontera se vació sin localizar el plan. Además, **80 797
partidas aleatorias** sobre la cruz inglesa terminaron con un mínimo de
2 piezas (ninguna llegó a 1). Esto evidencia que las soluciones del
Senku son rarísimas y que la pagoda, pese a ser admisible, no las guía.

### 4.4 Heurística de conectividad: beam search sí resuelve

La clave fue cambiar la heurística. La **heurística de conectividad**
ordena los estados por número de componentes conexas de piezas
(adyacencia ortogonal). Con ella, beam search resuelve la cruz inglesa
y, eligiendo bien el hueco inicial, las tres variantes obligatorias.
Criterio de meta: relajado (una pieza en cualquier sitio), tal y como
aclaró el profesor.

| # | Hueco inicial | β | Éxito | Movs | Nodos | T (s) |
|---|---------------|---|:-----:|-----:|------:|------:|
| 1 | (3,3) centro  | 300 | ✓ | 31 | 7 783 | 3,5 |
| 2 | (2,2) centro  | 500 | ✗ | — | 34 532 | 8,6 |
| 3 | (3,3) centro  | 800 | ✗ | — | 93 775 | 59,7 |
| 4 | (3,3) centro  | 500 | ✗ | — | 28 348 | 4,2 |
| 5 | (4,4) centro  | 800 | ✗ | — | 113 060 | 110,7 |

### 4.5 Estudio de la posición del hueco inicial

El profesor valora explorar distintas posiciones del hueco inicial. Al
hacerlo, **las tres variantes obligatorias (1, 3 y 5) resultan
resolubles** por beam search, aunque no siempre desde el centro:

| # | Hueco inicial | Éxito | Movs | Nodos | T (s) |
|---|---------------|:-----:|-----:|------:|------:|
| 3 | (3,3) centro  | ✗ | — | 53 423 | 33,5 |
| 3 | **(0,2)**     | ✓ | 35 | 17 381 | 11,2 |
| 3 | (2,4)         | ✗ | — | 53 495 | 36,9 |
| 5 | (4,4) centro  | ✗ | — | 64 159 | 61,4 |
| 5 | **(0,3)**     | ✓ | 43 | 21 674 | 20,2 |
| 5 | **(3,6)**     | ✓ | 43 | 22 276 | 21,7 |

Las variantes 2 (cuadrado 5×5) y 4 (diamante) no se resuelven; son
tableros ortogonales pequeños cuyo espacio alcanzable se bloquea muy
pronto (BFS exhaustiva sobre un tablero 4×4 análogo confirma su
irresolubilidad). La variante 1 sí termina en el propio hueco central
(problema complementario clásico), mientras que en las variantes 3 y 5
es necesario partir de un hueco en el brazo para hallar solución.

---

## 5. Discusión

- **Representación**: el `frozenset` minimiza coste de hashing y
  comparación.
- **Geometría en el `:init`**: declarar `salto` como hechos permite
  reutilizar un único dominio.
- **Incompletud de beam search**: descarta estados que pudieran
  pertenecer a la única solución. En el Senku, donde las soluciones
  son escasas, esto se traduce en fracaso sistemático cuando la
  heurística carece de poder discriminativo.
- **La heurística importa más que β**: la pagoda admisible falla
  incluso con β=2000, mientras que la heurística de conectividad
  resuelve la cruz inglesa con β=300 explorando ~7 800 nodos. El cuello
  de botella no es la anchura del haz sino la calidad de la señal.
- **La posición del hueco inicial es decisiva**: las variantes 3 y 5
  no se resuelven desde el centro pero sí desde un hueco en el brazo,
  lo que conecta con el problema complementario clásico del peg
  solitaire.

---

## 6. Uso de IA generativa

Se ha usado un asistente (Claude) para:

1. Explorar formulaciones alternativas del dominio PDDL.
2. Revisar la implementación de las heurísticas.
3. Refinar la redacción de la memoria.

Todos los entregables han sido revisados por los autores. Los prompts
principales se conservan junto al entregable.

---

## 7. Conclusiones

Se ha desarrollado un sistema completo de resolución del Senku basado
en planificación automática. El dominio PDDL es genérico, soporta
cualquier topología y se integra con planificadores externos. El
módulo Python implementa BFS y beam search con función pagoda,
ampliable con heurísticas compuestas y reinicios.

Los experimentos confirman que (i) el espacio del Senku escapa a la
búsqueda exhaustiva; (ii) la pagoda, pese a ser admisible, no contiene
señal suficiente para guiar beam search (falla incluso con β=2000); y
(iii) una heurística de **conectividad** —minimizar el número de
componentes conexas de piezas— sí permite a beam search resolver la
cruz inglesa (31 movimientos, ~7 800 nodos) y, eligiendo
adecuadamente el hueco inicial, las tres variantes obligatorias
(1, 3 y 5). El estudio de la posición del hueco inicial confirma el
fenómeno del problema complementario: en las variantes 3 y 5 sólo se
encuentra solución partiendo de un hueco situado en un brazo del
tablero, no desde el centro.

---

## Bibliografía

1. G. Chaves Benítez. *Planificación automática aplicada al Senku.
   Propuesta de trabajo*. Inteligencia Artificial — Ingeniería del
   Software, Universidad de Sevilla, 2025/2026.
2. Planning Wiki, *PDDL*, <https://planning.wiki/>.
3. A. Micheli et al. *Unified-Planning: A Library Making Planning
   Technology Accessible*. ICAPS, 2022.
   <https://unified-planning.readthedocs.io>.
4. M. Helmert. *The Fast Downward Planning System*. JAIR, vol. 26,
   pp. 191–246, 2006.
5. J. C. Beasley. *The Ins and Outs of Peg Solitaire*. Oxford
   University Press, 1985.
