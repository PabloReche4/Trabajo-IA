"""Heuristicas para el beam search."""

from typing import Callable, Dict, Iterable, Tuple

from .estado import Estado, ProblemaSenku
from .tableros import Coord, Tablero


PesosPagoda = Dict[Coord, int]


def pagoda_uniforme(tablero: Tablero) -> PesosPagoda:
    return {c: 1 for c in tablero.casillas}


def pagoda_clasica(tablero: Tablero) -> PesosPagoda:
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
    return sum(pesos[c] for c in estado if c in pesos)


def heuristica_pagoda(
    problema: ProblemaSenku, pesos: PesosPagoda
) -> Callable[[Estado], float]:
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
    movibles = set()
    for desde, sobre, hasta in problema.saltos:
        if desde in estado and sobre in estado and hasta not in estado:
            movibles.add(desde)
            movibles.add(sobre)
    return len(estado) - len(estado & movibles)


def heuristica_aislamiento(problema: ProblemaSenku) -> Callable[[Estado], int]:
    def h(estado: Estado) -> int:
        return _piezas_aisladas(estado, problema)
    return h


def _componentes_conexas(estado: Estado) -> int:
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
