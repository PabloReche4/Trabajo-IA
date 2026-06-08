"""Representacion de estados del Senku y motor de transiciones.

Un estado es un frozenset con las coordenadas de las casillas ocupadas.
El conjunto de casillas y la lista de saltos validos se sacan del
tablero. Usar frozensets nos permite usar los estados como claves de
diccionario (visitados, padres...) y comparar igualdad en O(1)
amortizado.
"""

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, List, Optional, Tuple

from .tableros import Coord, Tablero


Estado = FrozenSet[Coord]
Movimiento = Tuple[Coord, Coord, Coord]  # (desde, sobre, hasta)


@dataclass(frozen=True)
class ProblemaSenku:
    """Tablero + estado inicial + meta. Es lo que consumen las busquedas.

    Se construye desde un Tablero (`desde_tablero`) o desde un par de
    ficheros PDDL (ver lector_pddl.py).

    modo_relajado:
      - False (estricto): hay que dejar las casillas en `meta_ocupadas`
        ocupadas y las de `meta_vacias` vacias. Es la meta clasica.
      - True (relajado): basta con que quede una unica pieza en
        cualquier sitio del tablero. Es la version del enunciado tras
        la aclaracion del profesor.
    """

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
        """Genera (movimiento, nuevo_estado) para cada salto aplicable."""
        for desde, sobre, hasta in self.saltos:
            if desde in estado and sobre in estado and hasta not in estado:
                nuevo = (estado - {desde, sobre}) | {hasta}
                yield (desde, sobre, hasta), nuevo


def reconstruye_camino(
    padres: dict, estado_final: Estado
) -> Tuple[List[Estado], List[Movimiento]]:
    """Recompone la secuencia de estados y movimientos hacia atras.

    `padres[estado]` es (movimiento, estado_padre), o None para el
    estado inicial.
    """
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
