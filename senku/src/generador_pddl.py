"""Generacion de ficheros .pddl de problemas de Senku a partir de un Tablero.

El dominio es siempre el mismo (`dominio_senku.pddl`); este modulo se
encarga de producir, dada una variante, un fichero de problema PDDL con
sus objetos, estado inicial y meta.
"""

from pathlib import Path
from typing import Iterable

from .tableros import Tablero, nombre_casilla


def _bloque(predicados: Iterable[str], sangria: str = "    ") -> str:
    return "\n".join(f"{sangria}{p}" for p in predicados)


def problema_a_pddl(tablero: Tablero) -> str:
    """Devuelve la representacion PDDL del problema asociado al tablero."""
    objetos = sorted(nombre_casilla(c) for c in tablero.casillas)
    ocupadas = [f"(ocupada {nombre_casilla(c)})" for c in sorted(tablero.inicial_ocupadas)]
    vacias = [f"(vacia {nombre_casilla(c)})" for c in sorted(tablero.inicial_vacias)]
    saltos = [
        f"(salto {nombre_casilla(d)} {nombre_casilla(s)} {nombre_casilla(h)})"
        for d, s, h in tablero.saltos()
    ]
    meta_ocupadas = [f"(ocupada {nombre_casilla(c)})" for c in sorted(tablero.meta_ocupadas)]
    meta_vacias = [f"(vacia {nombre_casilla(c)})" for c in sorted(tablero.meta_vacias)]
    meta = meta_ocupadas + meta_vacias

    objetos_txt = _bloque(objetos)
    inicial_txt = _bloque(ocupadas + vacias + saltos)
    meta_txt = _bloque(meta, sangria="      ")

    return (
        "(define\n"
        f"  (problem {tablero.nombre})\n"
        "  (:domain senku)\n"
        "  (:objects\n"
        f"{objetos_txt}\n"
        "  )\n"
        "  (:init\n"
        f"{inicial_txt}\n"
        "  )\n"
        "  (:goal (and\n"
        f"{meta_txt}\n"
        "    )\n"
        "  )\n"
        ")\n"
    )


def escribe_problema(tablero: Tablero, destino: Path) -> Path:
    """Escribe el problema PDDL en disco y devuelve la ruta resultante."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(problema_a_pddl(tablero), encoding="utf-8")
    return destino
