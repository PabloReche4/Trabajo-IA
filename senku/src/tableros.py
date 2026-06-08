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


def _octogono() -> Tablero:
    """Variante 1: tablero octogonal de 37 posiciones (OBLIGATORIA).

            . . .
          . . . . .
        . . . . . . .
        . . . O . . .
        . . . . . . .
          . . . . .
            . . .

    Caja 7x7. Numero de casillas por fila (de arriba abajo):
    3, 5, 7, 7, 7, 5, 3. Total 37 casillas (36 fichas + 1 hueco).
    El hueco inicial se situa una fila por encima del centro geometrico
    del tablero. En coordenadas 0-indexed corresponde a la fila 2,
    columna 3 (esto es, fila 3 / columna 4 contando desde 1).
    El centro geometrico (fila 3, col 3 en 0-indexed) si lleva ficha.
    """
    anchos = [(0, 2, 4), (1, 1, 5), (2, 0, 6),
              (3, 0, 6), (4, 0, 6),
              (5, 1, 5), (6, 2, 4)]
    casillas: Set[Coord] = set()
    for fila, c_min, c_max in anchos:
        for c in range(c_min, c_max + 1):
            casillas.add((fila, c))
    return _tablero("variante_1_octogono", casillas, hueco=(2, 3), objetivo=(2, 3))


def _cruz_griega_grande() -> Tablero:
    """Variante 2: cruz griega grande de 45 posiciones.

            . . .
            . . .
            . . .
      . . . . . . . . .
      . . . . O . . . .
      . . . . . . . . .
            . . .
            . . .
            . . .

    Caja 9x9. Casillas por fila: 3, 3, 3, 9, 9, 9, 3, 3, 3. Total 45
    casillas. Los brazos verticales ocupan columnas 3, 4 y 5
    (0-indexed) y los horizontales filas 3, 4 y 5. El hueco inicial
    esta en el centro exacto (fila 4, col 4 en 0-indexed).
    """
    casillas: Set[Coord] = set()
    # Brazos horizontales (filas 3, 4, 5): toda la anchura
    for r in range(3, 6):
        for c in range(9):
            casillas.add((r, c))
    # Brazos verticales (columnas 3, 4, 5): toda la altura
    for c in range(3, 6):
        for r in range(9):
            casillas.add((r, c))
    return _tablero("variante_2_cruz_griega_grande", casillas,
                    hueco=(4, 4), objetivo=(4, 4))


def _cruz_asimetrica() -> Tablero:
    """Variante 3: cruz asimetrica de 39 posiciones (OBLIGATORIA).

            . . .
            . . .
            . . .
      . . . . . . . .
      . . . . O . . .
      . . . . . . . .
            . . .
            . . .

    Caja 8x8. Casillas por fila: 3, 3, 3, 8, 8, 8, 3, 3.
    Total 39 casillas (38 fichas + 1 hueco).

    Es una cruz NO simetrica:
      - Brazo vertical: columnas 2, 3, 4 (0-indexed).
      - Brazo horizontal: filas 3, 4, 5 (0-indexed).
      - Quedan 2 casillas a la izquierda del brazo vertical (cols 0, 1)
        y 3 a la derecha (cols 5, 6, 7).
      - 3 filas por encima del brazo horizontal (filas 0, 1, 2) frente
        a 2 por debajo (filas 6, 7).

    Hueco inicial: fila 4, col 3 en 0-indexed (= fila 5, col 4 en
    1-indexed segun el enunciado).
    """
    casillas: Set[Coord] = set()
    # Brazo vertical (cols 2, 3, 4 ocupan TODAS las filas 0..7)
    for r in range(8):
        for c in range(2, 5):
            casillas.add((r, c))
    # Brazo horizontal (filas 3, 4, 5 ocupan TODAS las columnas 0..7)
    for r in range(3, 6):
        for c in range(8):
            casillas.add((r, c))
    return _tablero("variante_3_cruz_asimetrica", casillas,
                    hueco=(4, 3), objetivo=(4, 3))


def _cruz_griega_clasica() -> Tablero:
    """Variante 4: cruz griega clasica (Senku ingles) de 33 posiciones.

            . . .
            . . .
        . . . . . . .
        . . . O . . .
        . . . . . . .
            . . .
            . . .

    Caja 7x7. Casillas por fila: 3, 3, 7, 7, 7, 3, 3.
    Total 33 casillas (32 fichas + 1 hueco). Hueco en el centro
    exacto (fila 3, col 3 en 0-indexed). Es el tablero canonico del
    Senku occidental, ampliamente estudiado en la literatura clasica.
    """
    casillas = {
        (r, c)
        for r in range(7)
        for c in range(7)
        if (2 <= r <= 4) or (2 <= c <= 4)
    }
    return _tablero("variante_4_cruz_griega_clasica", casillas,
                    hueco=(3, 3), objetivo=(3, 3))


def _rombo() -> Tablero:
    """Variante 5: rombo / diamante de 41 posiciones (OBLIGATORIA).

              .
            . . .
          . . . . .
        . . . . . . .
      . . . . O . . . .
        . . . . . . .
          . . . . .
            . . .
              .

    Caja 9x9. Casillas por fila: 1, 3, 5, 7, 9, 7, 5, 3, 1.
    Total 41 casillas (40 fichas + 1 hueco). Se construye a partir de
    la distancia de Manhattan al centro (|r-4| + |c-4| <= 4 en
    0-indexed). Hueco inicial en el centro exacto (fila 4, col 4 en
    0-indexed).
    """
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
