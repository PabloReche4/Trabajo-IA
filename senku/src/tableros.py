"""Definicion de los tableros del Senku.

Cada tablero es un conjunto de coordenadas (fila, columna) que indican
las casillas existentes. Sobre esas casillas se define el estado inicial
(piezas y hueco) y la meta a alcanzar.

La propuesta de trabajo (Figura 3) muestra cinco variantes del Senku.
Como las imagenes no especifican coordenadas exactas, en este modulo se
implementa una interpretacion razonada y documentada de cada una. La
codificacion permite reproducirlas trivialmente y ampliar el conjunto
con nuevas variantes si se desea.

Variantes implementadas:
    1. Cruz inglesa estandar (33 posiciones)
    2. Tablero cuadrado 5x5 (25 posiciones)
    3. Tablero octogonal europeo (37 posiciones)
    4. Tablero diamante de Manhattan-3 (25 posiciones)
    5. Cruz extendida (45 posiciones)

Para la convocatoria de junio se exige resolver al menos las variantes
1, 3 y 5 (las restantes se incluyen como soporte para experimentacion).
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Set, Tuple


Coord = Tuple[int, int]


@dataclass(frozen=True)
class Tablero:
    """Descripcion completa de un tablero de Senku.

    Atributos:
        nombre: identificador legible del tablero.
        casillas: coordenadas (fila, columna) presentes en el tablero.
        inicial_ocupadas: casillas con pieza al inicio.
        inicial_vacias: casillas vacias al inicio (huecos).
        meta_ocupadas: casillas que deben tener pieza en el estado meta.
        meta_vacias: casillas que deben estar vacias en el estado meta.
    """

    nombre: str
    casillas: FrozenSet[Coord]
    inicial_ocupadas: FrozenSet[Coord]
    inicial_vacias: FrozenSet[Coord]
    meta_ocupadas: FrozenSet[Coord]
    meta_vacias: FrozenSet[Coord]

    def saltos(self):
        """Genera todas las ternas (desde, sobre, hasta) consecutivas
        alineadas vertical u horizontalmente dentro del tablero."""
        for r, c in self.casillas:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                sobre = (r + dr, c + dc)
                hasta = (r + 2 * dr, c + 2 * dc)
                if sobre in self.casillas and hasta in self.casillas:
                    yield ((r, c), sobre, hasta)


def _tablero(nombre: str, casillas: Set[Coord], hueco: Coord, objetivo: Coord) -> Tablero:
    """Constructor auxiliar: define un tablero con un unico hueco inicial
    y exigencia de terminar con una unica pieza en la posicion `objetivo`."""
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


def _cruz_inglesa() -> Tablero:
    """Variante 1: cruz inglesa clasica de 33 posiciones.

            . . .
            . . .
        . . . . . . .
        . . . O . . .
        . . . . . . .
            . . .
            . . .

    Hueco inicial en el centro, objetivo: una unica pieza en el centro.
    Es el tablero canonico del Senku occidental.
    """
    casillas = {
        (r, c)
        for r in range(7)
        for c in range(7)
        if (2 <= r <= 4) or (2 <= c <= 4)
    }
    return _tablero("variante_1_cruz_inglesa", casillas, hueco=(3, 3), objetivo=(3, 3))


def _cuadrado_5x5() -> Tablero:
    """Variante 2: tablero cuadrado 5x5 de 25 posiciones, hueco central.

        . . . . .
        . . . . .
        . . O . .
        . . . . .
        . . . . .

    Variante mas pequena, util para experimentacion rapida y validacion.
    """
    casillas = {(r, c) for r in range(5) for c in range(5)}
    return _tablero("variante_2_cuadrado_5x5", casillas, hueco=(2, 2), objetivo=(2, 2))


def _octagonal_europeo() -> Tablero:
    """Variante 3: tablero octogonal europeo de 37 posiciones.

            . . .
          . . . . .
        . . . . . . .
        . . . O . . .
        . . . . . . .
          . . . . .
            . . .

    Se construye como un octagono inscrito en una rejilla 7x7,
    recortando triangulos de las cuatro esquinas. Filas 0 y 6 tienen
    3 casillas; filas 1 y 5 tienen 5; filas 2, 3, 4 tienen 7. Total 37.
    Es la disposicion ampliamente utilizada en la Europa continental.
    """
    anchos = [(0, 2, 4), (1, 1, 5), (2, 0, 6), (3, 0, 6),
              (4, 0, 6), (5, 1, 5), (6, 2, 4)]
    casillas: Set[Coord] = set()
    for fila, c_min, c_max in anchos:
        for c in range(c_min, c_max + 1):
            casillas.add((fila, c))
    return _tablero("variante_3_octagonal_europeo", casillas, hueco=(3, 3), objetivo=(3, 3))


def _diamante() -> Tablero:
    """Variante 4: tablero diamante de 25 posiciones (Manhattan <= 4).

              .
            . . .
          . . . . .
        . . . . . . .
          . . . . .
            . . .
              .

    Forma de rombo con el hueco en el centro. Util como variante de
    tamano intermedio entre el 5x5 y la cruz inglesa.
    """
    casillas = {(r, c) for r in range(7) for c in range(7) if abs(r - 3) + abs(c - 3) <= 3}
    return _tablero("variante_4_diamante", casillas, hueco=(3, 3), objetivo=(3, 3))


def _cruz_extendida() -> Tablero:
    """Variante 5: cruz extendida de 45 posiciones.

            . . .
            . . .
            . . .
      . . . . . . . . .
      . . . . O . . . .
      . . . . . . . . .
            . . .
            . . .
            . . .

    Cruz mas grande que la inglesa, con brazos de 3 celdas de ancho y
    3 celdas de profundidad fuera del cuadrado central 3x3. El hueco
    inicial se situa en el centro y el objetivo es terminar con una
    unica pieza en el centro. Es la variante mas grande del conjunto.
    """
    casillas: Set[Coord] = set()
    # Brazos horizontales (filas 3, 4, 5)
    for r in range(3, 6):
        for c in range(9):
            casillas.add((r, c))
    # Brazos verticales (columnas 3, 4, 5)
    for c in range(3, 6):
        for r in range(9):
            casillas.add((r, c))
    return _tablero("variante_5_cruz_extendida", casillas, hueco=(4, 4), objetivo=(4, 4))


TABLEROS: Dict[int, Tablero] = {
    1: _cruz_inglesa(),
    2: _cuadrado_5x5(),
    3: _octagonal_europeo(),
    4: _diamante(),
    5: _cruz_extendida(),
}


# Las variantes obligatorias para la convocatoria de junio (1, 3 y 5)
VARIANTES_OBLIGATORIAS = (1, 3, 5)


def obtener_tablero(numero: int) -> Tablero:
    """Devuelve la variante de tablero indicada (1 a 5)."""
    if numero not in TABLEROS:
        raise ValueError(f"Variante {numero} no definida. Usa 1..5.")
    return TABLEROS[numero]


def nombre_casilla(coord: Coord) -> str:
    """Genera el identificador PDDL de una casilla a partir de su coordenada."""
    r, c = coord
    return f"p_{r}_{c}"


def dibuja_tablero(tablero: Tablero, ocupadas: FrozenSet[Coord]) -> str:
    """Devuelve una representacion textual del tablero, marcando las
    casillas ocupadas con un punto y las vacias con un circulo."""
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
