# Presentación — Planificación automática aplicada al Senku
**Convocatoria de junio | Curso 2025/2026**

*Pablo Reche Gabaldón y [Nombre del compañero/a]*

Tiempo objetivo: 10 minutos. Cada miembro presenta 5 minutos.

---

## Slide 1 — Portada (10 s)

- Título del trabajo
- Asignatura, convocatoria, autores

---

## Slide 2 — El juego del Senku (45 s)

- Tablero con M casillas, M-1 piezas y 1 hueco.
- Movimiento: saltar una pieza adyacente; la pieza saltada se elimina.
- Objetivo clásico: dejar una única pieza en el hueco inicial.
- Versión relajada: dejar una única pieza en cualquier lugar.
- *Imagen: cruz inglesa estándar (33 casillas), antes y después.*

---

## Slide 3 — Por qué planificación automática (45 s)

- Acciones discretas, deterministas y completamente observables.
- Espacio de estados representable como árbol/grafo.
- PDDL (Planning Domain Definition Language) es el estándar para
  describir dominios y problemas.
- Encaja perfectamente en planificación clásica STRIPS.

---

## Slide 4 — Dominio PDDL (1 min)

```pddl
(define (domain senku)
  (:requirements :strips)
  (:predicates
    (ocupada ?p)
    (vacia ?p)
    (salto ?desde ?sobre ?hasta)
  )
  (:action mover
    :parameters (?desde ?sobre ?hasta)
    :precondition (and (salto ?desde ?sobre ?hasta)
                       (ocupada ?desde) (ocupada ?sobre) (vacia ?hasta))
    :effect (and (not (ocupada ?desde)) (vacia ?desde)
                 (not (ocupada ?sobre)) (vacia ?sobre)
                 (not (vacia ?hasta)) (ocupada ?hasta))))
```

- Diseño: `salto` como hechos estáticos del :init para mantener el
  dominio independiente de la topología del tablero. Una sola
  definición sirve para cualquier variante.

---

## Slide 5 — Las 5 variantes implementadas (45 s)

| # | Nombre              | Casillas | Obligatoria |
|---|---------------------|---------:|-------------|
| 1 | Cruz inglesa        |       33 | ✅           |
| 2 | Cuadrado 5×5        |       25 | —           |
| 3 | Octogonal europeo   |       37 | ✅           |
| 4 | Diamante            |       25 | —           |
| 5 | Cruz extendida      |       45 | ✅           |

*Las 2 y 4 son auxiliares para experimentación; 1, 3 y 5 son las
exigidas por el enunciado.*

---

## Slide 6 — Arquitectura del sistema (1 min)

```
+----------------+        +-----------------+
|  dominio.pddl  | -----> |   lector_pddl   |
+----------------+        |  (unified-pl    |
+----------------+        |   o ligero)     |
| problema.pddl  | -----> +--------+--------+
+----------------+                 |
                                   v
              +-------------- ProblemaSenku --------------+
              |                                          |
              v                                          v
      +-----------------+                      +-----------------+
      |     BFS         |                      |  Beam Search    |
      | (parte común)   |                      | (convocatoria   |
      |                 |                      |  de junio)      |
      +-----------------+                      +--------+--------+
                                                        |
                                              heurística pagoda /
                                              compuesta + reinicios
```

- CLI: `python -m senku.src.cli resolver --dominio ... --problema ... --beta 200`

---

## Slide 7 — Función pagoda (1 min)

- Asignación π : Casillas → ℤ⁺ tal que **π(a) + π(b) ≥ π(c)** para
  toda terna (a, b, c) alineada y consecutiva.
- Valor pagoda del estado: Π(s) = Σ_{p∈s} π(p).
- **Propiedad clave**: Π(s) es monótono no creciente con cada jugada.
- Por tanto h(s) = max(0, Π(s) − Π_meta) es una **heurística
  admisible**.
- Dos asignaciones implementadas:
  - Uniforme: π ≡ 1 (≡ número de piezas).
  - Clásica: π(r, c) = max(1, 8 − d_∞) con d_∞ = distancia de
    Chebyshev al baricentro.

---

## Slide 8 — Beam Search (1 min)

Pseudocódigo:

```
frontera ← {s_0}
while frontera no vacía:
    candidatos ← ∅
    for s in frontera:
        for s' en sucesores(s):
            if es_meta(s'): return plan
            candidatos ← candidatos ∪ {(h(s'), s')}
    ordenar candidatos por h
    frontera ← primeros β estados
return fallo
```

- Anchura del haz β: parámetro crítico.
- **Incompleto**: descarta estados que pudieran formar parte de la
  única solución.

---

## Slide 9 — Mitigaciones (45 s)

- **Heurística compuesta**: pagoda + aislamiento (×1000) + compacidad
  (×0,1). El término de aislamiento penaliza estados con piezas que ya
  no pueden eliminarse (callejones sin salida).
- **Reinicios estocásticos**: ejecutar el algoritmo varias veces con
  semillas distintas para el desempate.
- **Modo relajado**: meta = una pieza en cualquier sitio. Amplía el
  conjunto de soluciones.

---

## Slide 10 — Resultados (1 min)

| Var. | Algoritmo | Heur. | Nodos  | t (s) |
|-----:|-----------|-------|-------:|------:|
| 1    | Beam      | pag.  | 12 576 |  2,04 |
| 1    | Beam      | comp. | 14 924 |  9,55 |
| 3    | Beam      | comp. | 17 918 | 25,68 |
| 5    | Beam      | comp. | 21 305 | 24,96 |

- **Ningún algoritmo alcanzó la meta** en las 5 variantes con β = 200.
- Experimento extremo: V1 con β = 2000 + 20 reinicios → 9,3·10⁵
  nodos, 31 iteraciones (la profundidad correcta), aún sin solución.

---

## Slide 11 — Conclusiones (45 s)

- El sistema implementa correctamente:
  - Dominio PDDL genérico para cualquier topología.
  - BFS como búsqueda básica y baseline.
  - Beam Search con pagoda (algoritmo de convocatoria de junio).
  - Lector PDDL con dos backends.
- **Hallazgo principal**: la pagoda es admisible pero no
  discriminativa. Las soluciones del Senku son muy escasas y beam
  search se atasca en callejones sin salida.
- Las mitigaciones (heurística compuesta, reinicios) mejoran pero no
  resuelven la incompletud.
- Línea futura: incorporar look-ahead o combinar con búsqueda local.

---

## Slide 12 — Demo (1 min)

```powershell
# Generar los PDDL
python -m senku.src.cli generar

# Resolver una variante
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_2.pddl `
    --beta 500 --intentos 5 --relajado
```

---

## Slide 13 — Preguntas (10 min)

Preguntas del profesor sobre la memoria y el código fuente.
Cada autor responde por separado para asegurar comprensión completa
del trabajo.
