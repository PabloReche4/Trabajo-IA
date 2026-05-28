"""Heuristicas para guiar la busqueda sobre estados de Senku.

La heuristica principal del trabajo es la **funcion pagoda**. Se asigna
a cada casilla un valor entero de manera que para tres casillas
consecutivas y alineadas a, b, c se cumpla a + b >= c. Bajo esa
condicion, el valor pagoda de un estado (suma de los valores de sus
casillas ocupadas) es no creciente con cada movimiento legal: cada salto
elimina dos piezas (en `desde` y `sobre`) y crea una en `hasta`, asi que
la variacion de pagoda es `valor(hasta) - valor(desde) - valor(sobre)`,
que por la propiedad anterior es <= 0.

Eso convierte a la pagoda en una herramienta para detectar estados
"sin salida" (cuando su pagoda no alcanza la meta) y, sobre todo, como
heuristica admisible: cuanto mayor sea el exceso de pagoda sobre la
pagoda objetivo, mas piezas "improductivas" hay que eliminar.

Adicionalmente se proporcionan dos heuristicas no admisibles pero utiles
como senales de busqueda en algoritmos incompletos como beam search:

    - `heuristica_aislamiento`: penaliza estados con piezas que no
      pueden participar en ningun movimiento (callejones sin salida).
    - `heuristica_compacidad`: premia los estados donde las piezas
      restantes estan cerca de la posicion meta.

La funcion `heuristica_compuesta` combina pagoda con las dos anteriores;
es la heuristica recomendada cuando se quiere maximizar la probabilidad
de exito del beam search a costa de perder la cota admisible.
"""

from typing import Callable, Dict, Iterable, Tuple

from .estado import Estado, ProblemaSenku
from .tableros import Coord, Tablero


PesosPagoda = Dict[Coord, int]


def pagoda_uniforme(tablero: Tablero) -> PesosPagoda:
    """Asignacion trivial: todas las casillas valen 1.

    Cumple a + b >= c (1 + 1 >= 1). El valor pagoda coincide con el
    numero de piezas en el tablero, asi que se comporta como una
    heuristica que solo mide cuantas piezas faltan por eliminar.
    """
    return {c: 1 for c in tablero.casillas}


def pagoda_clasica(tablero: Tablero) -> PesosPagoda:
    """Asignacion clasica basada en la distancia de Chebyshev al centro.

    Para cada casilla se asigna peso `max(1, 8 - d)` donde `d` es la
    distancia de Chebyshev al baricentro del tablero. Las casillas
    centrales valen 8 (el maximo) y las del borde se reducen hasta 1.

    La condicion a + b >= c se cumple porque, en cualquier terna
    alineada y consecutiva, los pesos extremos suman al menos el peso
    intermedio (la diferencia de distancia de Chebyshev entre celdas
    contiguas es a lo sumo 1, por lo que sus pesos difieren en a lo
    sumo 1; en el peor caso a = 7, b = 8, c = 7, y 7 + 8 >= 7).
    """
    if not tablero.casillas:
        return {}
    filas = [r for r, _ in tablero.casillas]
    cols = [c for _, c in tablero.casillas]
    centro_r = (min(filas) + max(filas)) // 2
    centro_c = (min(cols) + max(cols)) // 2
    pesos: PesosPagoda = {}
    for (r, c) in tablero.casillas:
        d = max(abs(r - centro_r), abs(c - centro_c))
        pesos[(r, c)] = max(1, 8 - d)
    return pesos


def valor_pagoda(estado: Estado, pesos: PesosPagoda) -> int:
    """Suma de los valores pagoda de las casillas ocupadas en el estado."""
    return sum(pesos[c] for c in estado if c in pesos)


def heuristica_pagoda(
    problema: ProblemaSenku, pesos: PesosPagoda
) -> Callable[[Estado], float]:
    """Construye una heuristica h(estado) basada en la diferencia entre
    la pagoda del estado y la pagoda objetivo.

    La pagoda objetivo es la suma de los pesos de las casillas que deben
    estar ocupadas en la meta. Cuanto mas pagoda excedente tenga un
    estado, mas piezas innecesarias hay que eliminar para llegar a la
    meta, asi que la heuristica devuelve `max(0, pagoda(estado) - pagoda_meta)`.
    Si la pagoda es estrictamente menor que la objetivo el estado es
    infactible (no podra alcanzarse meta) y la heuristica devuelve inf.

    En modo relajado (cualquier pieza vale), la pagoda objetivo se toma
    como el peso minimo de cualquier casilla, lo que mantiene la
    admisibilidad.
    """
    if problema.modo_relajado:
        pagoda_meta = min(pesos.values()) if pesos else 0
    else:
        pagoda_meta = sum(pesos[c] for c in problema.meta_ocupadas if c in pesos)

    def h(estado: Estado) -> float:
        v = valor_pagoda(estado, pesos)
        if v < pagoda_meta:
            return float("inf")
        return v - pagoda_meta

    return h


def _piezas_aisladas(estado: Estado, problema: ProblemaSenku) -> int:
    """Cuenta cuantas piezas del estado no pueden participar en ningun
    movimiento (ni como `desde`, ni como `sobre`, ni como `hasta`).

    Una pieza aislada nunca podra ser eliminada ni desplazada, lo que
    impide alcanzar estados con menos piezas que las "no aisladas".
    Es una senal fuerte de callejon sin salida."""
    movibles = set()
    for desde, sobre, hasta in problema.saltos:
        if desde in estado and sobre in estado and hasta not in estado:
            movibles.add(desde)
            movibles.add(sobre)
    return len(estado) - len(estado & movibles)


def heuristica_aislamiento(problema: ProblemaSenku) -> Callable[[Estado], int]:
    """Heuristica = numero de piezas aisladas en el estado."""

    def h(estado: Estado) -> int:
        return _piezas_aisladas(estado, problema)

    return h


def _componentes_conexas(estado: Estado) -> int:
    """Cuenta las componentes conexas del estado considerando adyacencia
    ortogonal (arriba, abajo, izquierda, derecha) entre casillas
    ocupadas.

    En el Senku, para reducir el tablero a una unica pieza es necesario
    que, a grandes rasgos, las piezas permanezcan "juntas": dos piezas
    separadas por huecos que no pueden cerrarse nunca podran fusionarse.
    Cada componente conexa adicional es, por tanto, un grupo que muy
    probablemente quede aislado al final. Minimizar el numero de
    componentes resulta ser una senal de busqueda mucho mas informativa
    que la pagoda para este problema."""
    restantes = set(estado)
    componentes = 0
    while restantes:
        componentes += 1
        pila = [restantes.pop()]
        while pila:
            r, c = pila.pop()
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                vecino = (r + dr, c + dc)
                if vecino in restantes:
                    restantes.discard(vecino)
                    pila.append(vecino)
    return componentes


def heuristica_conectividad(
    problema: ProblemaSenku,
    w_componentes: float = 50.0,
    w_aislamiento: float = 20.0,
    w_piezas: float = 1.0,
    w_meta: float = 0.5,
    umbral_meta: int = 8,
) -> Callable[[Estado], float]:
    """Heuristica basada en la conectividad del tablero.

    Combina cuatro terminos, en orden de importancia:
        1. numero de componentes conexas (dominante): cada componente
           extra es un grupo que tendera a quedar aislado;
        2. numero de piezas aisladas (sin movimiento posible);
        3. numero total de piezas (criterio de desempate fino);
        4. atraccion hacia la meta: solo en modo estricto y cuando
           quedan pocas piezas (<= `umbral_meta`), se anade la suma de
           distancias Manhattan a la casilla meta, para que el final de
           la partida se dirija a la posicion objetivo.

    Esta heuristica es la que permite a beam search resolver tableros
    grandes como la cruz inglesa, donde la pagoda por si sola fracasa.
    No es admisible, pero su poder discriminativo es muy superior. El
    termino de conectividad codifica la intuicion de que, para terminar
    con una sola pieza, el conjunto de piezas debe mantenerse cohesionado
    durante toda la partida."""
    # Centroide de la meta (solo se usa en modo estricto).
    if problema.meta_ocupadas:
        objetivo = next(iter(problema.meta_ocupadas))
    else:
        objetivo = None

    def h(estado: Estado) -> float:
        valor = (
            w_componentes * _componentes_conexas(estado)
            + w_aislamiento * _piezas_aisladas(estado, problema)
            + w_piezas * len(estado)
        )
        if (
            not problema.modo_relajado
            and objetivo is not None
            and len(estado) <= umbral_meta
        ):
            valor += w_meta * sum(
                abs(r - objetivo[0]) + abs(c - objetivo[1]) for r, c in estado
            )
        return valor

    return h


def heuristica_compacidad(problema: ProblemaSenku) -> Callable[[Estado], float]:
    """Heuristica basada en la distancia agregada al centro de la meta.

    Para cada pieza se calcula su distancia de Chebyshev al centroide
    de las casillas meta (o al baricentro del tablero si la meta no
    define posiciones concretas). Estados con piezas concentradas cerca
    del centro reciben valores pequenos."""
    if problema.meta_ocupadas:
        celdas_ref = problema.meta_ocupadas
    else:
        celdas_ref = problema.tablero.casillas
    cx = sum(r for r, _ in celdas_ref) / len(celdas_ref)
    cy = sum(c for _, c in celdas_ref) / len(celdas_ref)

    def h(estado: Estado) -> float:
        if not estado:
            return 0.0
        return sum(max(abs(r - cx), abs(c - cy)) for r, c in estado)

    return h


def heuristica_compuesta(
    problema: ProblemaSenku,
    pesos: PesosPagoda,
    w_pagoda: float = 1.0,
    w_aislamiento: float = 1000.0,
    w_compacidad: float = 0.1,
) -> Callable[[Estado], float]:
    """Combina pagoda, aislamiento y compacidad en una unica heuristica.

    La intuicion es:
        - la pagoda asegura monotonia y admisibilidad;
        - el aislamiento penaliza con fuerza estados "muertos";
        - la compacidad introduce una senal direccional hacia la meta.

    Los pesos por defecto se han ajustado para que el aislamiento domine
    la decision (es la principal causa de fracaso en beam search) y
    despues actuen pagoda y compacidad como criterios de afinado."""
    h_pag = heuristica_pagoda(problema, pesos)
    h_ais = heuristica_aislamiento(problema)
    h_com = heuristica_compacidad(problema)

    def h(estado: Estado) -> float:
        valor_pag = h_pag(estado)
        if valor_pag == float("inf"):
            return float("inf")
        return (
            w_pagoda * valor_pag
            + w_aislamiento * h_ais(estado)
            + w_compacidad * h_com(estado)
        )

    return h
