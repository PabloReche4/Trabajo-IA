"""Lectura de un par (dominio.pddl, problema.pddl) y conversion a la
representacion interna `ProblemaSenku`.

El requisito de la convocatoria de junio es que el sistema acepte dos
ficheros PDDL arbitrarios. Para ello se usa la biblioteca recomendada
en la asignatura, `unified_planning`, exactamente con la misma
metodologia mostrada en la Practica 4:

    from unified_planning.io import PDDLReader
    lector = PDDLReader()
    problema_up = lector.parse_problem(dominio_pddl, problema_pddl)

Despues se recorren los hechos del estado inicial y la meta del objeto
devuelto por la biblioteca para construir nuestro `ProblemaSenku`, que
es lo que consumen los algoritmos de busqueda.

Como red de seguridad se incluye un parser propio
(`carga_con_parser_ligero`) que solo entiende el dominio Senku. Se usa
unicamente si `unified_planning` no esta instalado en el entorno, lo
que no deberia ocurrir en la entrega (la asignatura usa esta biblioteca
en la Practica 4).
"""

from pathlib import Path
import re
from typing import List, Set

from .estado import Movimiento, ProblemaSenku
from .tableros import Coord, Tablero


def _parse_coord(nombre: str) -> Coord:
    """Convierte un identificador PDDL `p_R_C` en una coordenada (R, C).

    Se acepta indistintamente mayusculas y minusculas porque
    `unified_planning` normaliza los identificadores a minusculas al
    parsear el fichero PDDL."""
    partes = nombre.split("_")
    if len(partes) != 3 or partes[0].lower() != "p":
        raise ValueError(
            f"Nombre de casilla '{nombre}' no sigue el patron 'p_R_C'."
        )
    return int(partes[1]), int(partes[2])


# ---------------------------------------------------------------------------
# Backend principal: unified_planning (estilo Practica 4)
# ---------------------------------------------------------------------------


def carga_con_unified_planning(
    ruta_dominio: Path, ruta_problema: Path
) -> ProblemaSenku:
    """Carga un par dominio + problema PDDL usando `unified_planning`.

    La biblioteca se encarga de validar la sintaxis PDDL y devuelve un
    objeto `Problem` del que extraemos:
        - los objetos -> casillas del tablero;
        - los hechos `ocupada`, `vacia` del :init -> estado inicial;
        - los hechos `salto` del :init -> lista de movimientos posibles;
        - los hechos del :goal (con sus negaciones) -> casillas que
          deben quedar ocupadas o vacias en la meta.
    """
    from unified_planning.io import PDDLReader

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
        # `goal` puede ser un AND de hechos o un hecho aislado.
        hechos = list(goal.args) if goal.is_and() else [goal]
        for hecho in hechos:
            negado = hecho.is_not()
            if negado:
                hecho = hecho.args[0]
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
# Fallback: parser propio (sin dependencias)
# ---------------------------------------------------------------------------


_RE_TOKEN = re.compile(r"\(|\)|[^\s\(\)]+")


def _tokenize(texto: str) -> List[str]:
    sin_comentarios = re.sub(r";[^\n]*", "", texto)
    return _RE_TOKEN.findall(sin_comentarios)


def _parse_sexpr(tokens: List[str]):
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
    for nodo in arbol:
        if (
            isinstance(nodo, list)
            and nodo
            and isinstance(nodo[0], str)
            and nodo[0] == etiqueta
        ):
            return nodo[1:]
    return []


def carga_con_parser_ligero(
    ruta_dominio: Path, ruta_problema: Path
) -> ProblemaSenku:
    ruta_dominio = Path(ruta_dominio)
    if not ruta_dominio.exists():
        raise FileNotFoundError(f"No existe el dominio: {ruta_dominio}")

    texto = Path(ruta_problema).read_text(encoding="utf-8")
    arbol = _parse_sexpr(_tokenize(texto))
    if not isinstance(arbol, list) or not arbol or arbol[0] != "define":
        raise ValueError("El fichero no parece un problema PDDL valido")

    nombre_problema = "problema_pddl"
    for nodo in arbol[1:]:
        if isinstance(nodo, list) and nodo and nodo[0] == "problem":
            nombre_problema = nodo[1]

    init_section = _extrae_seccion(arbol[1:], ":init")
    init = [n for n in init_section if isinstance(n, list)]
    goal_section = _extrae_seccion(arbol[1:], ":goal")
    if not goal_section:
        goal_hechos = []
    else:
        nodo = goal_section[0]
        goal_hechos = nodo[1:] if isinstance(nodo, list) and nodo and nodo[0] == "and" else [nodo]

    casillas: Set[Coord] = set()
    ocupadas: Set[Coord] = set()
    vacias: Set[Coord] = set()
    saltos: List[Movimiento] = []
    for hecho in init:
        if hecho[0] == "ocupada":
            c = _parse_coord(hecho[1]); casillas.add(c); ocupadas.add(c)
        elif hecho[0] == "vacia":
            c = _parse_coord(hecho[1]); casillas.add(c); vacias.add(c)
        elif hecho[0] == "salto":
            t = tuple(_parse_coord(x) for x in hecho[1:])
            casillas.update(t); saltos.append(t)

    meta_ocupadas: Set[Coord] = set()
    meta_vacias: Set[Coord] = set()
    for hecho in goal_hechos:
        negado = hecho[0] == "not"
        if negado:
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

    En el contexto de la asignatura, el backend por defecto es siempre
    `unified_planning`. Si no esta disponible, se cae al parser ligero
    propio. El parametro `backend` permite forzar uno u otro
    explicitamente."""
    if backend in {"auto", "unified_planning"}:
        try:
            return carga_con_unified_planning(ruta_dominio, ruta_problema)
        except ImportError:
            if backend == "unified_planning":
                raise
            return carga_con_parser_ligero(ruta_dominio, ruta_problema)
    if backend == "ligero":
        return carga_con_parser_ligero(ruta_dominio, ruta_problema)
    raise ValueError(f"Backend desconocido: {backend}")
