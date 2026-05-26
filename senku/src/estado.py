"""Representacion de estados del Senku y motor de transiciones.

Un estado se representa como un frozenset con las coordenadas de las
casillas ocupadas. El conjunto de casillas posibles y la lista de saltos
validos se derivan del tablero. Esta representacion es independiente del
PDDL: usar frozensets permite usar los estados como claves de diccionario
y comparar la igualdad en tiempo constante (amortizado).
"""

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, List, Optional, Tuple

from .tableros import Coord, Tablero


Estado = FrozenSet[Coord]
Movimiento = Tuple[Coord, Coord, Coord]  # (desde, sobre, hasta)


@dataclass(frozen=True)
class ProblemaSenku:
    """Encapsula un tablero junto a su estado inicial y meta.

    Esta clase es la interfaz comun que consumen los algoritmos de
    busqueda. Se puede construir directamente desde un objeto Tablero o
    bien desde un par de ficheros PDDL (ver `lector_pddl.py`).

    El campo `modo_relajado` permite cambiar el criterio de meta:
        - False (estricto): el estado meta exige que las casillas en
          `meta_ocupadas` esten ocupadas y las casillas en `meta_vacias`
          esten vacias (definicion clasica).
        - True (relajado): la meta se cumple en cuanto queda una unica
          pieza en cualquier lugar del tablero. Es la version relajada
          mencionada en el enunciado y resulta solucionable en mas
          tableros, ya que evita las obstrucciones de paridad cuando la
          casilla objetivo coincide con el hueco inicial.
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
    """Reconstruye la secuencia de estados y movimientos desde el padre
    hasta el estado final usando el diccionario `padres`.

    `padres[estado]` debe ser (movimiento, estado_padre) o None para el
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
