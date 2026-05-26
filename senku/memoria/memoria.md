# Planificación automática aplicada al Senku
**Convocatoria de junio — Curso 2025/2026**

*Pablo Reche Gabaldón y [Nombre del compañero/a]*
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

| # | Nombre                       | Casillas | Hueco | Obligatoria |
|---|------------------------------|---------:|-------|-------------|
| 1 | Cruz inglesa estándar        |       33 | centro| Sí          |
| 2 | Cuadrado 5×5                 |       25 | centro| No          |
| 3 | Octogonal europeo            |       37 | centro| Sí          |
| 4 | Diamante (Manhattan-3)       |       25 | centro| No          |
| 5 | Cruz extendida               |       45 | centro| Sí          |

### 4.2 Resultados principales

| # | Algoritmo | Heur.     | Nodos  | Tiempo (s) |
|---|-----------|-----------|-------:|-----------:|
| 1 | BFS       | —         | 30 001 | 2,76       |
| 1 | Beam      | pagoda    | 12 576 | 2,04       |
| 1 | Beam      | compuesta | 14 924 | 9,55       |
| 2 | BFS       | —         | 30 001 | 2,63       |
| 2 | Beam      | pagoda    | 9 208  | 0,89       |
| 2 | Beam      | compuesta | 10 790 | 4,81       |
| 3 | BFS       | —         | 30 001 | 4,27       |
| 3 | Beam      | pagoda    | 14 710 | 4,06       |
| 3 | Beam      | compuesta | 17 918 | 25,68      |
| 4 | BFS       | —         | 30 001 | 1,99       |
| 4 | Beam      | pagoda    | 7 931  | 0,84       |
| 4 | Beam      | compuesta | 8 842  | 3,57       |
| 5 | BFS       | —         | 30 001 | 6,12       |
| 5 | Beam      | pagoda    | 18 547 | 6,45       |
| 5 | Beam      | compuesta | 21 305 | 24,96      |

*BFS limitada a 30 000 nodos; Beam con β=200, 3 reinicios, máximo 80 iteraciones. Ninguna configuración alcanzó la meta en modo estricto.*

Experimento de fuerza bruta: variante 1 con β=2000 y 20 reinicios
estocásticos. Beam search exploró ~9,3·10⁵ nodos en 584 s alcanzando
las 31 iteraciones (profundidad equivalente al plan óptimo), pero la
frontera se vació sin localizar el plan. Confirma empíricamente la
incompletud del algoritmo en problemas de soluciones raras como el
Senku clásico.

### 4.3 Modo relajado

Con meta "una pieza en cualquier sitio", el espacio de soluciones
crece y beam search obtiene más éxitos. El cuaderno incluye los
resultados.

---

## 5. Discusión

- **Representación**: el `frozenset` minimiza coste de hashing y
  comparación.
- **Geometría en el `:init`**: declarar `salto` como hechos permite
  reutilizar un único dominio.
- **Incompletud de beam search**: descarta estados que pudieran
  pertenecer a la única solución. En el Senku, donde las soluciones
  son escasas, esto se traduce en fracaso sistemático cuando la
  heurística carece de poder discriminativo. Las mitigaciones
  (compuesta + reinicios) alivian, no eliminan, este problema.

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
búsqueda exhaustiva y (ii) la incompletud de beam search se hace muy
patente en problemas con escasas soluciones. La pagoda proporciona
una cota admisible útil pero, por sí sola, es insuficiente como señal
de búsqueda; combinarla con términos no admisibles mejora claramente
el rendimiento sin romper la estructura del algoritmo original.

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
