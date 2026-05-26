"""Lectura de un par (dominio.pddl, problema.pddl) y conversion a la
representacion interna `ProblemaSenku`.

El requisito de la convocatoria de junio es que el sistema acepte dos
ficheros PDDL arbitrarios. Para ello se proporcionan dos backends:

    - `carga_con_unified_planning`: utiliza la biblioteca
      `unified_planning` (recomendada en la asignatura). Recomendable
      cuando esta disponible porque valida la sintaxis PDDL completa y
      es la misma que se usa en la Practica 4.
    - `carga_con_parser_ligero`: parser propio especifico para el
      dominio Senku usado en este trabajo. Solo soporta los predicados
      `ocupada`, `vacia` y `salto` y los goals con conjunciones de los
      mismos predicados (o sus negaciones). Util en entornos donde
      `unified_planning` no esta instalado.

`carga_problema_pddl` selecciona automaticamente el primero disponible.
"""

from pathlib import Path
import re
from typing import List, Set, Tuple

from .estado import Movimiento, ProblemaSenku
from .tableros import Coord, Tablero


def _parse_coord(nombre: str) -> Coord:
    """Convierte un identificador PDDL `p_R_C` en una coordenada (R, C)."""
    partes = nombre.split("_")
    if len(partes) != 3 or partes[0].lower() != "p":
        raise ValueError(
            f"Nombre de casilla '{nombre}' no sigue el patron 'p_R_C'."
        )
    return int(partes[1]), int(partes[2])


# ---------------------------------------------------------------------------
# Backend basado en unified_planning
# ---------------------------------------------------------------------------


def carga_con_unified_planning(ruta_dominio: Path, ruta_problema: Path) -> ProblemaSenku:
    from unified_planning.io import PDDLReader  # importacion diferida

    lector = PDDLReader()
    problema_up = lector.parse_problem(str(ruta_dominio), str(ruta_problema))

    casillas: Set[Coord] = set()
    ocupadas: Set[Coord] = set()
    vacias: Set[Coord] = set()
    saltos: List[Movimiento] = []

    for fluente_inicial, valor in problema_up.explicit_initial_values.items():
        if not bool(valor):
            continue
        nombre = fluente_inicial.fluent().name
        args = [_parse_coord(str(a)) for a in fluente_inicial.args]
        if nombre == "ocupada":
            casillas.add(args[0]); ocupadas.add(args[0])
        elif nombre == "vacia":
            casillas.add(args[0]); vacias.add(args[0])
        elif nombre == "salto":
            casillas.update(args); saltos.append(tuple(args))

    meta_ocupadas: Set[Coord] = set()
    meta_vacias: Set[Coord] = set()
    for goal in problema_up.goals:
        hechos = list(goal.args) if goal.is_and() else [goal]
        for hecho in hechos:
            if hecho.is_not():
                negado = True
                hecho = hecho.args[0]
            else:
                negado = False
            nombre = hecho.fluent().name
            args = [_parse_coord(str(a)) for a in hecho.args]
            if nombre == "ocupada":
                (meta_vacias if negado else meta_ocupadas).add(args[0])
            elif nombre == "vacia":
                (meta_ocupadas if negado else meta_vacias).add(args[0])

    tablero = Tablero(
        nombre=problema_up.name,
        casillas=frozenset(casillas),
        inicial_ocupadas=frozenset(ocupadas),
        inicial_vacias=frozenset(vacias),
        meta_ocupadas=frozenset(meta_ocupadas),
        meta_vacias=frozenset(meta_vacias),
    )
    return ProblemaSenku(
        tablero=tablero,
        inicial=frozenset(ocupadas),
        meta_ocupadas=frozenset(meta_ocupadas),
        meta_vacias=frozenset(meta_vacias),
        saltos=tuple(saltos),
    )


# ---------------------------------------------------------------------------
# Parser ligero propio
# ---------------------------------------------------------------------------


_RE_TOKEN = re.compile(r"\(|\)|[^\s\(\)]+")


def _tokenize(texto: str) -> List[str]:
    # Eliminar comentarios PDDL (todo desde ; hasta fin de linea)
    sin_comentarios = re.sub(r";[^\n]*", "", texto)
    return _RE_TOKEN.findall(sin_comentarios)


def _parse_sexpr(tokens: List[str]):
    """Convierte una lista de tokens en una S-expresion anidada."""
    if not tokens:
        raise ValueError("Tokens agotados al parsear S-expresion")
    token = tokens.pop(0)
    if token == "(":
        lista = []
        while tokens and tokens[0] != ")":
            lista.append(_parse_sexpr(tokens))
        if not tokens:
            raise ValueError("Falta parentesis de cierre")
        tokens.pop(0)
        return lista
    if token == ")":
        raise ValueError("Parentesis de cierre inesperado")
    return token


def _extrae_seccion(arbol, etiqueta):
    """Devuelve la primera sub-lista cuyo primer elemento coincide con
    `etiqueta` (las secciones de PDDL empiezan por `:objects`, `:init`,
    `:goal`, etc.)."""
    for nodo in arbol:
        if isinstance(nodo, list) and nodo and isinstance(nodo[0], str) and nodo[0] == etiqueta:
            return nodo[1:]
    return []


def _hechos_de_init(seccion_init):
    """Devuelve los hechos del estado inicial. Cada hecho es una lista
    ['predicado', 'arg1', 'arg2', ...]."""
    return [n for n in seccion_init if isinstance(n, list)]


def _hechos_de_goal(seccion_goal):
    """Aplana el goal: admite forma `(and h1 h2 ...)` o un solo hecho."""
    if not seccion_goal:
        return []
    nodo = seccion_goal[0]
    if isinstance(nodo, list) and nodo and nodo[0] == "and":
        return nodo[1:]
    return [nodo]


def carga_con_parser_ligero(ruta_dominio: Path, ruta_problema: Path) -> ProblemaSenku:
    # El dominio no se usa para construir el problema (asumimos el dominio
    # estandar de Senku), pero comprobamos que existe para detectar
    # errores tempranos del usuario.
    ruta_dominio = Path(ruta_dominio)
    if not ruta_dominio.exists():
        raise FileNotFoundError(f"No existe el dominio: {ruta_dominio}")

    texto = Path(ruta_problema).read_text(encoding="utf-8")
    tokens = _tokenize(texto)
    arbol = _parse_sexpr(tokens)
    if not isinstance(arbol, list) or not arbol or arbol[0] != "define":
        raise ValueError("El fichero no parece un problema PDDL valido")

    nombre_problema = "problema_pddl"
    for nodo in arbol[1:]:
        if isinstance(nodo, list) and nodo and nodo[0] == "problem":
            nombre_problema = nodo[1]

    init = _hechos_de_init(_extrae_seccion(arbol[1:], ":init"))
    goal_hechos = _hechos_de_goal(_extrae_seccion(arbol[1:], ":goal"))

    casillas: Set[Coord] = set()
    ocupadas: Set[Coord] = set()
    vacias: Set[Coord] = set()
    saltos: List[Movimiento] = []
    for hecho in init:
        if hecho[0] == "ocupada":
            c = _parse_coord(hecho[1])
            casillas.add(c); ocupadas.add(c)
        elif hecho[0] == "vacia":
            c = _parse_coord(hecho[1])
            casillas.add(c); vacias.add(c)
        elif hecho[0] == "salto":
            terna = tuple(_parse_coord(t) for t in hecho[1:])
            casillas.update(terna); saltos.append(terna)

    meta_ocupadas: Set[Coord] = set()
    meta_vacias: Set[Coord] = set()
    for hecho in goal_hechos:
        negado = False
        if hecho[0] == "not":
            negado = True
            hecho = hecho[1]
        if hecho[0] == "ocupada":
            c = _parse_coord(hecho[1])
            (meta_vacias if negado else meta_ocupadas).add(c)
        elif hecho[0] == "vacia":
            c = _parse_coord(hecho[1])
            (meta_ocupadas if negado else meta_vacias).add(c)

    tablero = Tablero(
        nombre=nombre_problema,
        casillas=frozenset(casillas),
        inicial_ocupadas=frozenset(ocupadas),
        inicial_vacias=frozenset(vacias),
        meta_ocupadas=frozenset(meta_ocupadas),
        meta_vacias=frozenset(meta_vacias),
    )
    return ProblemaSenku(
        tablero=tablero,
        inicial=frozenset(ocupadas),
        meta_ocupadas=frozenset(meta_ocupadas),
        meta_vacias=frozenset(meta_vacias),
        saltos=tuple(saltos),
    )


# ---------------------------------------------------------------------------
# Selector automatico
# ---------------------------------------------------------------------------


def carga_problema_pddl(
    ruta_dominio: Path,
    ruta_problema: Path,
    backend: str = "auto",
) -> ProblemaSenku:
    """Carga un par dominio + problema PDDL.

    Parametros:
        backend: "auto" (por defecto), "unified_planning" o "ligero".
            En modo "auto" intenta primero `unified_planning` y si no
            esta disponible cae al parser ligero.
    """
    if backend == "auto":
        try:
            return carga_con_unified_planning(ruta_dominio, ruta_problema)
        except ImportError:
            return carga_con_parser_ligero(ruta_dominio, ruta_problema)
    if backend == "unified_planning":
        return carga_con_unified_planning(ruta_dominio, ruta_problema)
    if backend == "ligero":
        return carga_con_parser_ligero(ruta_dominio, ruta_problema)
    raise ValueError(f"Backend desconocido: {backend}")
