"""Generacion de ficheros .pddl de problemas de Senku."""

from pathlib import Path
from typing import Iterable

from .tableros import Tablero, nombre_casilla


def _bloque(predicados: Iterable[str], sangria: str = "    ") -> str:
    return "\n".join(f"{sangria}{p}" for p in predicados)


def problema_a_pddl(tablero: Tablero) -> str:
    objetos = sorted(nombre_casilla(c) for c in tablero.casillas)
    ocupadas = [
        f"(ocupada {nombre_casilla(c)})" for c in sorted(tablero.inicial_ocupadas)
    ]
    vacias = [
        f"(vacia {nombre_casilla(c)})" for c in sorted(tablero.inicial_vacias)
    ]
    saltos = [
        f"(salto {nombre_casilla(d)} {nombre_casilla(s)} {nombre_casilla(h)})"
        for d, s, h in tablero.saltos()
    ]
    meta = [
        f"(ocupada {nombre_casilla(c)})" for c in sorted(tablero.meta_ocupadas)
    ] + [
        f"(vacia {nombre_casilla(c)})" for c in sorted(tablero.meta_vacias)
    ]
    return (
        "(define\n"
        f"  (problem {tablero.nombre})\n"
        "  (:domain senku)\n"
        "  (:objects\n"
        f"{_bloque(objetos)}\n"
        "  )\n"
        "  (:init\n"
        f"{_bloque(ocupadas + vacias + saltos)}\n"
        "  )\n"
        "  (:goal (and\n"
        f"{_bloque(meta, sangria='      ')}\n"
        "    )\n"
        "  )\n"
        ")\n"
    )


def escribe_problema(tablero: Tablero, destino: Path) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(problema_a_pddl(tablero), encoding="utf-8")
    return destino


def escribe_dominio_y_problema_con_writer(
    tablero: Tablero,
    destino_dominio: Path,
    destino_problema: Path,
) -> None:
    from unified_planning.io import PDDLWriter
    from .dominio_up import construye_problema_up

    problema_up = construye_problema_up(tablero)
    escritor = PDDLWriter(problema_up)
    Path(destino_dominio).parent.mkdir(parents=True, exist_ok=True)
    Path(destino_problema).parent.mkdir(parents=True, exist_ok=True)
    escritor.write_domain(str(destino_dominio))
    escritor.write_problem(str(destino_problema))
