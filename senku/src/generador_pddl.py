"""Generacion de ficheros .pddl de problemas de Senku.

Hay dos caminos, alineados con la Practica 4:

  1. escribe_problema(tablero, destino): escribimos el .pddl del
     problema a mano, referenciando el dominio compartido `senku` que
     vive en senku/pddl/dominio_senku.pddl. Es el formato que mantiene
     la asignatura: un solo dominio para todas las variantes. Camino
     por defecto.

  2. escribe_dominio_y_problema_con_writer(tablero, dom, prob):
     construye el Problem con la API Python de unified-planning (en
     dominio_up.py) y lo serializa con PDDLWriter, igual que en la
     Practica 4. Devuelve un dominio + problema autocontenidos. Util
     si se quiere ensenar el flujo de la biblioteca o pasarle el
     resultado directamente a Fast Downward.
"""

from pathlib import Path
from typing import Iterable

from .tableros import Tablero, nombre_casilla


# ---------------------------------------------------------------------------
# Camino 1: escritor manual con dominio compartido `senku`
# ---------------------------------------------------------------------------


def _bloque(predicados: Iterable[str], sangria: str = "    ") -> str:
    return "\n".join(f"{sangria}{p}" for p in predicados)


def problema_a_pddl(tablero: Tablero) -> str:
    """PDDL del problema (no del dominio) asociado al tablero.

    Apunta al dominio compartido `senku` (dominio_senku.pddl), de modo
    que todas las variantes comparten dominio."""
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
    """Escribe el problema PDDL en disco usando el escritor manual."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(problema_a_pddl(tablero), encoding="utf-8")
    return destino


# ---------------------------------------------------------------------------
# Camino 2: PDDLWriter de unified-planning (estilo Practica 4)
# ---------------------------------------------------------------------------


def escribe_dominio_y_problema_con_writer(
    tablero: Tablero,
    destino_dominio: Path,
    destino_problema: Path,
) -> None:
    """Genera ambos ficheros via PDDLWriter de unified-planning.

    Sigue la receta de la Practica 4:

        from unified_planning.io import PDDLWriter
        escritor = PDDLWriter(problema)
        escritor.write_domain('dominio.pddl')
        escritor.write_problem('problema.pddl')

    Los nombres del dominio y el problema en el .pddl resultante seran
    los que asigne la libreria a partir del nombre del Problem (por
    defecto, `<nombre>-domain` y `<nombre>-problem`).
    """
    from unified_planning.io import PDDLWriter
    from .dominio_up import construye_problema_up

    problema_up = construye_problema_up(tablero)
    escritor = PDDLWriter(problema_up)
    Path(destino_dominio).parent.mkdir(parents=True, exist_ok=True)
    Path(destino_problema).parent.mkdir(parents=True, exist_ok=True)
    escritor.write_domain(str(destino_dominio))
    escritor.write_problem(str(destino_problema))
