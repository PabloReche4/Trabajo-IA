"""Tableros del Senku (las 5 variantes de la Figura 3)."""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Set, Tuple


Coord = Tuple[int, int]


@dataclass(frozen=True)
class Tablero:
    nombre: str
    casillas: FrozenSet[Coord]
    inicial_ocupadas: FrozenSet[Coord]
    inicial_vacias: FrozenSet[Coord]
    meta_ocupadas: FrozenSet[Coord]
    meta_vacias: FrozenSet[Coord]

    def saltos(self):
        for r, c in self.casillas:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                sobre = (r + dr, c + dc)
                hasta = (r + 2 * dr, c + 2 * dc)
                if sobre in self.casillas and hasta in self.casillas:
                    yield ((r, c), sobre, hasta)


def _tablero(nombre: str, casillas: Set[Coord], hueco: Coord, objetivo: Coord) -> Tablero:
    casillas_fz = frozenset(casillas)
    inicial_ocupadas = casillas_fz - {hueco}
    meta_ocupadas = frozenset({objetivo})
    meta_vacias = casillas_fz - meta_ocupadas
    return Tablero(
        nombre=nombre,
        casillas=casillas_fz,
        inicial_ocupadas=frozenset(inicial_ocupadas),
        inicial_vacias=frozenset({hueco}),
        meta_ocupadas=meta_ocupadas,
        meta_vacias=meta_vacias,
    )


def _octogono() -> Tablero:
    # Variante 1 (obligatoria): caja 7x7, casillas por fila 3,5,7,7,7,5,3.
    anchos = [(0, 2, 4), (1, 1, 5), (2, 0, 6),
              (3, 0, 6), (4, 0, 6),
              (5, 1, 5), (6, 2, 4)]
    casillas: Set[Coord] = set()
    for fila, c_min, c_max in anchos:
        for c in range(c_min, c_max + 1):
            casillas.add((fila, c))
    return _tablero("variante_1_octogono", casillas, hueco=(2, 3), objetivo=(2, 3))


def _cruz_griega_grande() -> Tablero:
    # Variante 2: caja 9x9, casillas por fila 3,3,3,9,9,9,3,3,3.
    casillas: Set[Coord] = set()
    for r in range(3, 6):
        for c in range(9):
            casillas.add((r, c))
    for c in range(3, 6):
        for r in range(9):
            casillas.add((r, c))
    return _tablero("variante_2_cruz_griega_grande", casillas,
                    hueco=(4, 4), objetivo=(4, 4))


def _cruz_asimetrica() -> Tablero:
    # Variante 3 (obligatoria): caja 8x8, brazo vertical en cols 2-4,
    # brazo horizontal en filas 3-5.
    casillas: Set[Coord] = set()
    for r in range(8):
        for c in range(2, 5):
            casillas.add((r, c))
    for r in range(3, 6):
        for c in range(8):
            casillas.add((r, c))
    return _tablero("variante_3_cruz_asimetrica", casillas,
                    hueco=(4, 3), objetivo=(4, 3))


def _cruz_griega_clasica() -> Tablero:
    # Variante 4: Senku clasico ingles, 33 casillas.
    casillas = {
        (r, c)
        for r in range(7)
        for c in range(7)
        if (2 <= r <= 4) or (2 <= c <= 4)
    }
    return _tablero("variante_4_cruz_griega_clasica", casillas,
                    hueco=(3, 3), objetivo=(3, 3))


def _rombo() -> Tablero:
    # Variante 5 (obligatoria): rombo definido por |r-4| + |c-4| <= 4.
    casillas = {(r, c) for r in range(9) for c in range(9)
                if abs(r - 4) + abs(c - 4) <= 4}
    return _tablero("variante_5_rombo", casillas,
                    hueco=(4, 4), objetivo=(4, 4))


TABLEROS: Dict[int, Tablero] = {
    1: _octogono(),
    2: _cruz_griega_grande(),
    3: _cruz_asimetrica(),
    4: _cruz_griega_clasica(),
    5: _rombo(),
}


VARIANTES_OBLIGATORIAS = (1, 3, 5)


def obtener_tablero(numero: int) -> Tablero:
    if numero not in TABLEROS:
        raise ValueError(f"Variante {numero} no definida. Usa 1..5.")
    return TABLEROS[numero]


def nombre_casilla(coord: Coord) -> str:
    r, c = coord
    return f"p_{r}_{c}"


def dibuja_tablero(tablero: Tablero, ocupadas: FrozenSet[Coord]) -> str:
    if not tablero.casillas:
        return ""
    filas = {r for r, _ in tablero.casillas}
    cols = {c for _, c in tablero.casillas}
    salida = []
    for r in range(min(filas), max(filas) + 1):
        linea = []
        for c in range(min(cols), max(cols) + 1):
            if (r, c) not in tablero.casillas:
                linea.append(" ")
            elif (r, c) in ocupadas:
                linea.append("o")
            else:
                linea.append(".")
        salida.append(" ".join(linea))
    return "\n".join(salida)
