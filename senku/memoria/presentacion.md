# Presentación — Planificación automática aplicada al Senku
**Convocatoria de junio | Curso 2025/2026**

*Pablo Reche Gabaldón y Sol Villegas Charlo*

Tiempo objetivo: ~10 minutos. Reparto sugerido: alternando para que el
tribunal vea que ambos miembros dominan el trabajo.

---

## Slide 1 — Portada (10 s) — *Pablo*

**Contenido de la slide:**
- Título del trabajo
- Asignatura, convocatoria, autores

**Qué decir:**

> "Buenas tardes. Somos Pablo Reche y Sol Villegas, y nuestro trabajo de
> la convocatoria de junio es la **planificación automática aplicada al
> Senku**."

Solo eso. No te entretengas.

---

## Slide 2 — El juego del Senku (45 s) — *Pablo*

**Contenido de la slide:**
- Tablero con M casillas, M-1 piezas y 1 hueco.
- Movimiento: saltar una pieza adyacente; la pieza saltada se elimina.
- Objetivo clásico: dejar una única pieza en el hueco inicial.
- Versión relajada: dejar una única pieza en cualquier lugar.
- *Imagen: cruz inglesa estándar (33 casillas), antes y después.*

**Qué decir:**

> "Antes de meternos en planificación, dos palabras sobre el juego, por
> si alguien no lo conoce. Es un solitario clásico: un tablero con M
> casillas, M menos 1 piezas y un único hueco. En cada turno cogemos una
> pieza, saltamos sobre otra adyacente —en vertical o en horizontal— y
> aterrizamos en el hueco contiguo. **La pieza saltada se elimina**. El
> objetivo clásico es terminar con una sola pieza en el hueco inicial.
> Existe también una versión relajada, que es la que valida el profesor,
> en la que basta con quedarse con una pieza en cualquier sitio."

Si tienes imagen de la cruz inglesa antes/después, apóyate en ella.

---

## Slide 3 — Por qué planificación automática (45 s) — *Pablo*

**Contenido de la slide:**
- Acciones discretas, deterministas y completamente observables.
- Espacio de estados representable como árbol/grafo.
- PDDL (Planning Domain Definition Language) es el estándar para
  describir dominios y problemas.
- Encaja perfectamente en planificación clásica STRIPS.

**Qué decir:**

> "El Senku encaja muy bien en planificación clásica por tres motivos:
> las acciones son **discretas**, **deterministas** y el entorno es
> **totalmente observable**. Cada estado es un nodo y cada salto válido
> una arista. Por eso usamos **PDDL**, que es el lenguaje estándar para
> describir dominios y problemas de planificación, y trabajamos en el
> nivel STRIPS. Esto nos permite separar el modelo del juego de la
> técnica de resolución y comparar nuestro beam search frente a
> planificadores genéricos como Fast Downward sobre el mismo PDDL."

---

## Slide 4 — Dominio PDDL (1 min) — *Pablo*

**Contenido de la slide:**

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

- Diseño: `salto` como hechos estáticos del `:init` para mantener el
  dominio independiente de la topología del tablero. Una sola
  definición sirve para cualquier variante.

**Qué decir:**

> "Aquí tenéis el dominio. Es muy compacto: **tres predicados**
> —`ocupada`, `vacia` y `salto`— y **una sola acción**, `mover`. Los dos
> primeros predicados son el estado dinámico de cada casilla. El
> tercero, `salto`, codifica la geometría del tablero, y este es el
> punto clave del diseño: **no aparece en las acciones como algo que
> cambie, sino como hechos estáticos** del `:init` de cada problema."
>
> "La consecuencia es que con un **único dominio** servimos cualquier
> topología. Para cambiar de tablero solo hace falta cambiar los hechos
> `salto` del problema. Si hubiéramos codificado la geometría dentro del
> dominio —con tipos por fila y columna, por ejemplo— habríamos perdido
> esa generalidad."

**Por si preguntan por alternativas:** valoramos tres opciones más:
tipos por fila/columna, tres acciones distintas según dirección, y
fluentes numéricos con PDDL 2.1. Las descartamos por complicar el
modelo sin aportar expresividad.

---

## Slide 5 — Las 5 variantes implementadas (45 s) — *Sol*

**Contenido de la slide:**

| # | Nombre                          | Caja | Cas. | Obligatoria |
|---|---------------------------------|------|-----:|-------------|
| 1 | Octógono                        | 7×7  |   37 | sí          |
| 2 | Cruz griega grande              | 9×9  |   45 | —           |
| 3 | Cruz asimétrica                 | 8×8  |   39 | sí          |
| 4 | Cruz griega clásica (inglesa)   | 7×7  |   33 | —           |
| 5 | Rombo / diamante                | 9×9  |   41 | sí          |

*Las 2 y 4 son auxiliares para experimentación; 1, 3 y 5 son las
exigidas por el enunciado (Figura 3, Sección 3.2).*

**Qué decir:**

> "Pasamos a las variantes. El enunciado pide en la Figura 3 cinco
> tableros distintos, y obliga a resolver el 1, el 3 y el 5. Nosotros
> las hemos implementado las cinco: el **octógono** de 37 casillas, la
> **cruz griega grande** de 45, la **cruz asimétrica** de 39, la **cruz
> inglesa clásica** de 33 —que es el Senku canónico, lo dejamos como
> referencia histórica— y el **rombo** de 41 casillas. La 2 y la 4 no
> son obligatorias, pero las incluimos como material adicional para
> tener más con lo que experimentar."

---

## Slide 6 — Arquitectura del sistema (1 min) — *Sol*

**Contenido de la slide:**

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

**Qué decir:**

> "Esta es la arquitectura. El sistema recibe **dos ficheros PDDL**
> —dominio y problema, como pide el enunciado—. El módulo `lector_pddl`
> los procesa: el camino principal es `unified_planning`, igual que en
> la Práctica 4, y hay un parser propio de S-expresiones como red de
> seguridad por si no estuviese instalada la biblioteca."
>
> "Lo que devuelve es un objeto `ProblemaSenku`, que es la representación
> interna que consumen los algoritmos. Hay dos motores: **BFS** para la
> parte común y **Beam Search** para la ampliación de junio, con tres
> variantes —clásico, con reinicios estocásticos y iterativo—. Encima,
> **Fast Downward** vía unified-planning como línea de base."
>
> "Y todo se accede desde una **interfaz de línea de comandos** que
> permite resolver un par PDDL cualquiera con cualquiera de los
> algoritmos."

---

## Slide 7 — Función pagoda (1 min) — *Sol*

**Contenido de la slide:**

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

**Qué decir:**

> "Vamos a la heurística que pide el enunciado, la **función pagoda**,
> introducida por Conway. La idea: asignamos a cada casilla un peso
> entero positivo tal que, para cualquier terna de casillas consecutivas
> y alineadas (a, b, c), se cumpla **π(a) + π(b) ≥ π(c)**."
>
> "El **valor pagoda** de un estado es la suma de pesos de las piezas
> que tiene vivas. La propiedad fundamental es que **ese valor es
> monótono no creciente con cada jugada legal** —cualquier movimiento
> elimina dos piezas y crea una, y la condición π(a)+π(b)≥π(c) garantiza
> que la suma no aumenta—. De ahí sale una heurística admisible: el
> excedente respecto a la pagoda objetivo es el número mínimo de
> unidades que aún hay que descartar."
>
> "Hemos implementado dos asignaciones: la **uniforme**, todos los pesos
> a 1, que coincide con contar piezas; y la **clásica**, basada en la
> distancia de Chebyshev al baricentro, que premia las casillas
> centrales."

---

## Slide 8 — Beam Search (1 min) — *Pablo*

**Contenido de la slide:**

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

**Qué decir:**

> "Beam search es una variante de búsqueda en anchura con **memoria
> limitada**. En cada nivel mantenemos solo los β estados con mejor
> heurística y descartamos el resto sin posibilidad de recuperarlos."
>
> "El esquema lo veis en el pseudocódigo: arrancamos con la frontera
> igual al estado inicial; en cada iteración generamos todos los
> sucesores, los ordenamos por la heurística y nos quedamos con los β
> mejores como nueva frontera. El parámetro **β regula el equilibrio**
> entre memoria/tiempo y cobertura."
>
> "La pega es que **beam search es incompleto**: las trayectorias que
> conducen a la meta pueden quedar descartadas en algún nivel
> intermedio. Esto va a ser justamente el problema que abordamos en la
> siguiente diapositiva."

Además del clásico, hemos implementado **dos extensiones**: con
reinicios estocásticos (varias semillas distintas) e iterativo
(probando anchuras crecientes).

---

## Slide 9 — El problema de la pagoda y la solución (1 min) — *Pablo*

**Contenido de la slide:**

- La **pagoda es admisible** pero **no discrimina**: beam search falla
  incluso con β = 2000. En 80\,797 partidas aleatorias, ninguna llegó a
  1 pieza.
- **Heurística de conectividad** (la clave): minimizar el número de
  componentes conexas de piezas. Para terminar con una sola pieza, el
  conjunto debe mantenerse cohesionado.
- Además: **reinicios estocásticos** y **modo relajado** (meta = una
  pieza en cualquier sitio, criterio aclarado por el profesor).

**Qué decir:**

> "Aquí está el hallazgo central del trabajo. Resulta que **la pagoda,
> aunque es admisible, no funciona como guía de búsqueda en el Senku**.
> Lo probamos hasta β=2000 con veinte reinicios estocásticos y casi un
> millón de nodos explorados, y **no encuentra plan**. Para tener otra
> evidencia, lanzamos **80\,797 partidas con movimientos aleatorios**
> sobre la cruz inglesa: ninguna terminó con una sola pieza. Las
> soluciones son tan raras que la pagoda no las discrimina del resto de
> estados."
>
> "La solución fue cambiar de heurística. Diseñamos una **heurística de
> conectividad** basada en una intuición sencilla: para terminar con
> una sola pieza, las piezas restantes tienen que mantenerse en **una
> única componente conexa**. Si una se queda aislada del resto, el plan
> ya es imposible. Minimizar el número de componentes obliga al haz a
> priorizar trayectorias cohesionadas."
>
> "Con esto, más el **modo relajado** que aclaró el profesor y los
> **reinicios estocásticos**, beam search empieza a resolver."

---

## Slide 10 — Resultados (1 min) — *Sol*

**Contenido de la slide:**

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

**Qué decir:**

> "Pasamos a los resultados. La tabla resume el **barrido exhaustivo de
> huecos** que hicimos sobre las tres variantes obligatorias. La cruz
> asimétrica es resoluble desde **el 100% de los huecos**; el octógono
> desde un 46%; y el rombo solo desde un 20%."
>
> "Tres conclusiones rápidas. Primero, con la pagoda **no se resuelve
> ninguna variante**, ni siquiera con β=2000. Segundo, **la posición del
> hueco inicial es decisiva**: la cruz griega es resoluble desde
> cualquier hueco bajo simetría, pero en el rombo solo unos pocos huecos
> admiten plan."
>
> "Y la tercera, que es interesante: **nuestro beam search complementa a
> Fast Downward**. Fast Downward resuelve V3 y V4 en unos pocos
> segundos, pero **se atasca en V1, V2 y V5** incluso con timeouts de
> 300 segundos. Justo donde Fast Downward falla, nuestro beam search
> con conectividad sí encuentra plan. Es decir, no competimos contra
> FD, lo complementamos."

---

## Slide 11 — Conclusiones (45 s) — *Sol*

**Contenido de la slide:**

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

**Qué decir:**

> "Para terminar. Hemos montado un sistema completo de resolución del
> Senku basado en planificación automática: un **dominio PDDL genérico**
> que sirve para cualquier topología, **BFS** para la parte común,
> **beam search** para junio con tres variantes, y **Fast Downward**
> como línea de base."
>
> "El **hallazgo principal** es que la heurística pesa más que el
> tamaño del haz. La pagoda no basta; **la conectividad sí resuelve la
> cruz inglesa con β=300** y unas 7\,800 expansiones. Y el segundo
> hallazgo: **la posición del hueco inicial determina la solubilidad**
> de cada variante."
>
> "Como líneas futuras: look-ahead de uno o dos niveles, combinación
> con búsquedas locales estocásticas, y heurísticas basadas en
> *packings* combinatorios de la literatura clásica del peg solitaire."

---

## Slide 12 — Preguntas — *Ambos*

**Contenido de la slide:**

Preguntas del profesor sobre la memoria y el código fuente.
Cada autor responde por separado para asegurar comprensión completa
del trabajo.

**Qué decir:**

> "Esto es todo. Quedamos a vuestra disposición para preguntas."

A partir de aquí el profesor pregunta. Sol y Pablo respondéis cada uno
por separado para que se vea que ambos entendéis las decisiones.

---

## Preguntas previsibles y cómo encararlas

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué `salto` como hecho estático y no como predicado del dominio? | Para que el dominio sea independiente del tablero. Misma definición sirve para las 5 variantes. |
| ¿Por qué frozenset para los estados? | Hashable (sirve como clave de visitados), igualdad O(1), operaciones de conjunto baratas. |
| ¿Por qué la pagoda no basta? | Es admisible pero no discrimina: muchos estados intermedios reciben el mismo valor y el haz no puede priorizar. |
| ¿Por qué beam search es incompleto? | Porque descarta irreversiblemente todo lo que no entra en los β mejores; la única ruta puede haberse perdido. |
| ¿Qué hace beam search iterativo distinto? | Empieza con β pequeño y solo invierte más presupuesto si hace falta. Como iterative deepening pero sobre cobertura. |
| ¿Modo relajado vs estricto? | Estricto = pieza en posición concreta. Relajado = pieza en cualquier sitio. El profesor aclaró que vale el relajado. |
| ¿Por qué FD falla en V1, V2 y V5? | Geometrías más densas; el factor de ramificación crece y la heurística FF se diluye. |
| ¿`min_piezas_alcanzadas` para qué sirve? | Diagnosticar cuán cerca quedó beam search. Si llega a 1 hay solución; si se queda en 4+ es estructuralmente difícil. |
| ¿Por qué la heurística compuesta no es admisible? | Aislamiento y compacidad pueden sobreestimar la distancia a la meta. La sacrificamos por mejor poder discriminativo. |
| ¿Por qué la conectividad funciona? | Captura una invariante estructural: para llegar a 1 pieza, todas deben mantenerse cohesionadas en una sola componente conexa. |
| ¿Cómo está integrado Fast Downward? | Vía `unified_planning` con `OneshotPlanner('fast-downward')`, igual que en la Práctica 4. Hay un parche para el bug de codificación en Windows. |

---

## Consejos finales

- **Mira al tribunal, no a las diapositivas**. Llevad esto en notas, no
  leído.
- **Si os pillan en algo que no sabéis**, decid "no lo recuerdo ahora
  mismo, pero está en la memoria" — mejor que inventar.
- **Tiempo**: los slides 9 (problema y solución) y 10 (resultados) son
  los que más peso tienen. Si vais mal de tiempo, recortad de los
  slides 2-3 (intro).
- **Lleva la memoria impresa** o en otro dispositivo por si necesitas
  mirar un dato concreto.

Mucha suerte.
