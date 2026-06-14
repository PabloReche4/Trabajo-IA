"""Heuristicas para guiar la busqueda sobre estados de Senku.

La heuristica principal del trabajo es la *funcion pagoda*: se asigna a
cada casilla un peso entero de forma que, para toda terna (a, b, c) de
casillas consecutivas y alineadas, se cumpla a + b >= c. Bajo esa
condicion, el valor pagoda de un estado (suma de pesos de sus piezas)
es no creciente con cada salto legal.

Aparte de la pagoda, aqui hay tres heuristicas no admisibles pero utiles
como senal de busqueda en beam search:

  - heuristica_aislamiento: penaliza piezas sin movimiento posible.
  - heuristica_compacidad: premia estados con piezas cerca de la meta.
  - heuristica_conectividad: ordena por numero de componentes conexas
    (es la que acaba resolviendo la cruz inglesa).

heuristica_compuesta combina pagoda + aislamiento + compacidad; sirve
cuando se prefiere cobertura empirica a admisibilidad estricta.
"""

from typing import Callable, Dict, Iterable, Tuple

from .estado import Estado, ProblemaSenku
from .tableros import Coord, Tablero


PesosPagoda = Dict[Coord, int]


def pagoda_uniforme(tablero: Tablero) -> PesosPagoda:
    """Asignacion trivial: todas las casillas valen 1.

    Cumple a + b >= c y el valor pagoda coincide con el numero de piezas.
    """
    return {c: 1 for c in tablero.casillas}


def pagoda_clasica(tablero: Tablero) -> PesosPagoda:
    """Asignacion clasica basada en la distancia de Chebyshev al centro.

    Cada casilla recibe peso max(1, 8 - d) con d = distancia de Chebyshev
    al baricentro. El centro vale 8 y se va degradando hacia el borde
    hasta 1. La condicion a + b >= c se cumple porque pesos contiguos
    difieren en a lo sumo 1 (peor caso: 7 + 8 >= 7).
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
    """h(estado) = max(0, pagoda(estado) - pagoda_meta).

    Si la pagoda cae por debajo de la objetivo, el estado es infactible:
    devolvemos inf para que beam search lo descarte. En modo relajado la
    pagoda objetivo es el peso minimo del tablero (mantiene admisibilidad).
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
    """Cuenta piezas que no pueden participar en ningun movimiento.

    Una pieza es "movible" si aparece como desde o sobre de algun salto
    cuyo destino esta vacio. Las que no lo son nunca podran eliminarse:
    son una senal fuerte de callejon sin salida."""
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
    """Componentes conexas de las piezas por adyacencia ortogonal.

    Para llegar a 1 pieza hay que mantener el conjunto cohesionado: dos
    grupos separados por huecos no recuperables ya no se podran juntar.
    Cada componente extra es, en la practica, un grupo que se quedara
    atras."""
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

    Combina cuatro terminos por orden de importancia:
      1. componentes conexas (peso dominante);
      2. piezas aisladas (sin movimiento posible);
      3. numero total de piezas (desempate fino);
      4. solo en modo estricto y cuando quedan pocas piezas
         (<= umbral_meta), atraccion Manhattan a la casilla objetivo.

    No es admisible, pero es la unica con la que beam search resuelve
    la cruz inglesa."""
    # El centroide solo nos sirve en modo estricto (cuando hay meta posicional).
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
    """Suma de distancias Chebyshev de las piezas al centroide de la meta.

    Si la meta no define posiciones concretas, usamos el baricentro del
    tablero. Cuanto mas concentradas esten las piezas cerca del centro,
    menor valor recibe el estado."""
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
    """Pagoda + aislamiento + compacidad en una unica heuristica.

    - pagoda: aporta monotonia y admisibilidad (en su componente);
    - aislamiento: penaliza con fuerza estados "muertos";
    - compacidad: senal direccional hacia la meta.

    Los pesos por defecto hacen que el aislamiento domine la decision
    (es la principal causa de fracaso del beam) y dejan pagoda y
    compacidad como criterios de afinado."""
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
