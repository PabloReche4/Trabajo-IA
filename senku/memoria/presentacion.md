# Presentación — Planificación automática aplicada al Senku
**Convocatoria de junio | Curso 2025/2026**

*Pablo Reche Gabaldón y Sol Villegas Charlo*

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

| # | Nombre                          | Caja | Cas. | Obligatoria |
|---|---------------------------------|------|-----:|-------------|
| 1 | Octógono                        | 7×7  |   37 | ✅           |
| 2 | Cruz griega grande              | 9×9  |   45 | —           |
| 3 | Cruz asimétrica                 | 8×8  |   39 | ✅           |
| 4 | Cruz griega clásica (inglesa)   | 7×7  |   33 | —           |
| 5 | Rombo / diamante                | 9×9  |   41 | ✅           |

*Las 2 y 4 son auxiliares para experimentación; 1, 3 y 5 son las
exigidas por el enunciado (Figura 3, Sección 3.2).*

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

## Slide 9 — El problema de la pagoda y la solución (1 min)

- La **pagoda es admisible** pero **no discrimina**: beam search falla
  incluso con β = 2000. En 80 797 partidas aleatorias, ninguna llegó a
  1 pieza.
- **Heurística de conectividad** (la clave): minimizar el número de
  componentes conexas de piezas. Para terminar con una sola pieza, el
  conjunto debe mantenerse cohesionado.
- Además: **reinicios estocásticos** y **modo relajado** (meta = una
  pieza en cualquier sitio, criterio aclarado por el profesor).

---

## Slide 10 — Resultados (1 min)

Beam search **con la heurística de conectividad + iterativo** resuelve
las tres variantes obligatorias. Barrido exhaustivo de huecos:

| Var. | Tablero            | Casillas | Resolubles | %    |
|-----:|--------------------|---------:|-----------:|-----:|
| 1    | Octógono           | 37       | 6/13       | 46,2 |
| 3    | Cruz asimétrica    | 39       | **10/10**  | **100** |
| 5    | Rombo              | 41       | 3/15       | 20,0 |

- Con **pagoda**: ninguna variante se resuelve (ni con β = 2000).
- **La posición del hueco inicial es decisiva**: en V1 y V5 algunos
  huecos no admiten plan; V3 es resoluble desde cualquier hueco.
- **Beam search complementa a Fast Downward**: FD resuelve V3 (8s) y
  V4 (18s) pero falla en V1, V2 y V5 incluso con 300s; nuestro beam
  search + conectividad sí encuentra plan en V1 y V5.

---

## Slide 11 — Conclusiones (45 s)

- El sistema implementa correctamente:
  - Dominio PDDL genérico para cualquier topología.
  - BFS (parte común) y Beam Search (convocatoria de junio).
  - Lector PDDL con `unified_planning` + Fast Downward como baseline.
- **Hallazgo principal**: la heurística importa más que β. La pagoda no
  basta; la **conectividad** sí resuelve la cruz inglesa (β = 300).
- **La posición del hueco inicial** determina la solubilidad (V3, V5).
- Beam search es incompleto, pero con la heurística adecuada resuelve
  el problema del enunciado.
- Línea futura: look-ahead, búsqueda local, packings combinatorios.

---

## Slide 12 — Demo (1 min)

```powershell
# Generar los PDDL
python -m senku.src.cli generar

# Resolver variante 3 (cruz asimétrica, obligatoria)
python -m senku.src.cli resolver `
    --dominio senku/pddl/dominio_senku.pddl `
    --problema senku/pddl/problemas/variante_3.pddl `
    --algoritmo beam-iter --intentos 4 --relajado
```

---

## Slide 13 — Preguntas (10 min)

Preguntas del profesor sobre la memoria y el código fuente.
Cada autor responde por separado para asegurar comprensión completa
del trabajo.
