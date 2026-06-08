"""Representacion de estados del Senku."""

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, List, Optional, Tuple

from .tableros import Coord, Tablero


Estado = FrozenSet[Coord]
Movimiento = Tuple[Coord, Coord, Coord]


@dataclass(frozen=True)
class ProblemaSenku:
    tablero: Tablero
    inicial: Estado
    meta_ocupadas: Estado
    meta_vacias: Estado
    saltos: Tuple[Movimiento, ...]
    modo_relajado: bool = False

    @classmethod
    def desde_tablero(cls, tablero: Tablero, modo_relajado: bool = False) -> "ProblemaSenku":
        return cls(
            tablero=tablero,
            inicial=frozenset(tablero.inicial_ocupadas),
            meta_ocupadas=frozenset(tablero.meta_ocupadas),
            meta_vacias=frozenset(tablero.meta_vacias),
            saltos=tuple(tablero.saltos()),
            modo_relajado=modo_relajado,
        )

    def es_meta(self, estado: Estado) -> bool:
        if self.modo_relajado:
            return len(estado) == 1
        if not self.meta_ocupadas.issubset(estado):
            return False
        if estado & self.meta_vacias:
            return False
        return True

    def sucesores(self, estado: Estado) -> Iterable[Tuple[Movimiento, Estado]]:
        for desde, sobre, hasta in self.saltos:
            if desde in estado and sobre in estado and hasta not in estado:
                nuevo = (estado - {desde, sobre}) | {hasta}
                yield (desde, sobre, hasta), nuevo


def reconstruye_camino(
    padres: dict, estado_final: Estado
) -> Tuple[List[Estado], List[Movimiento]]:
    estados: List[Estado] = [estado_final]
    movimientos: List[Movimiento] = []
    actual = estado_final
    while padres.get(actual) is not None:
        movimiento, padre = padres[actual]
        movimientos.append(movimiento)
        estados.append(padre)
        actual = padre
    estados.reverse()
    movimientos.reverse()
    return estados, movimientos
