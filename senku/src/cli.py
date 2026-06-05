"""Interfaz de linea de comandos para resolver problemas de Senku.

Uso tipico (desde la raiz del proyecto):

    python -m senku.src.cli resolver \\
        --dominio senku/pddl/dominio_senku.pddl \\
        --problema senku/pddl/problemas/variante_3.pddl \\
        --beta 200 --intentos 5 --relajado

Comandos:
    resolver  Aplica el algoritmo elegido al par dominio+problema PDDL.
              Algoritmos disponibles:
                * beam (por defecto): beam search con la heuristica
                  pagoda (algoritmo de la convocatoria de junio).
                * bfs: busqueda en anchura (parte comun).
                * fd: Fast Downward via unified-planning (linea base).
    generar   Construye los ficheros .pddl de las cinco variantes
              definidas en el modulo `tableros`.
"""

import argparse
import sys
from pathlib import Path

from .busqueda import (
    beam_search_con_reinicios,
    beam_search_iterativo,
    busqueda_primero_anchura,
)
from .estado import ProblemaSenku
from .generador_pddl import escribe_problema
from .heuristicas import (
    heuristica_conectividad,
    heuristica_pagoda,
    pagoda_clasica,
    pagoda_uniforme,
)
from .lector_pddl import carga_problema_pddl
from .tableros import TABLEROS, nombre_casilla


def _formatea_movimientos(movimientos) -> str:
    return "\n".join(
        f"  {i + 1:3d}. mover {nombre_casilla(d)} {nombre_casilla(s)} {nombre_casilla(h)}"
        for i, (d, s, h) in enumerate(movimientos)
    )


def comando_resolver(args: argparse.Namespace) -> int:
    problema = carga_problema_pddl(
        Path(args.dominio), Path(args.problema), backend=args.backend
    )
    if args.relajado:
        problema = ProblemaSenku(
            tablero=problema.tablero,
            inicial=problema.inicial,
            meta_ocupadas=problema.meta_ocupadas,
            meta_vacias=problema.meta_vacias,
            saltos=problema.saltos,
            modo_relajado=True,
        )

    if args.algoritmo == "fd":
        return _resuelve_con_fd(args, problema)

    if args.heuristica == "conectividad":
        h = heuristica_conectividad(problema)
    else:
        pesos = (
            pagoda_clasica(problema.tablero)
            if args.pagoda == "clasica"
            else pagoda_uniforme(problema.tablero)
        )
        h = heuristica_pagoda(problema, pesos)

    if args.algoritmo == "bfs":
        resultado = busqueda_primero_anchura(problema, limite_nodos=args.limite)
    elif args.algoritmo == "beam-iter":
        # Variante con anchura creciente: empieza pequena y solo invierte
        # mas presupuesto si la instancia lo necesita.
        resultado = beam_search_iterativo(
            problema,
            heuristica=h,
            betas=[100, 300, 800, 1500],
            intentos_por_beta=args.intentos,
            iteraciones_maximas=args.limite,
            usar_visitados=not args.sin_visitados,
        )
    else:
        resultado = beam_search_con_reinicios(
            problema,
            heuristica=h,
            beta=args.beta,
            intentos=args.intentos,
            iteraciones_maximas=args.limite,
            usar_visitados=not args.sin_visitados,
        )
    print(resultado)
    if resultado.exito:
        print("Secuencia de movimientos:")
        print(_formatea_movimientos(resultado.movimientos))
        return 0
    return 1


def _resuelve_con_fd(args: argparse.Namespace, problema_interno) -> int:
    """Camino 'fd': delega en Fast Downward via unified-planning.

    Re-carga el problema PDDL en su forma original (el objeto Problem de
    unified-planning) y se lo pasa a `OneshotPlanner`."""
    from unified_planning.io import PDDLReader
    from .planificador import resuelve_con_fast_downward

    lector = PDDLReader()
    problema_up = lector.parse_problem(args.dominio, args.problema)
    r = resuelve_con_fast_downward(problema_up, busqueda=args.fd_search)
    print(r)
    if r.exito:
        print("Secuencia de movimientos:")
        for i, m in enumerate(r.movimientos):
            print(f"  {i + 1:3d}. {m}")
        return 0
    return 1


def comando_generar(args: argparse.Namespace) -> int:
    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)
    for numero, tablero in TABLEROS.items():
        ruta = destino / f"variante_{numero}.pddl"
        escribe_problema(tablero, ruta)
        print(f"Generado {ruta} ({len(tablero.casillas)} casillas)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sistema de resolucion del Senku basado en planificacion automatica."
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_resolver = subparsers.add_parser(
        "resolver",
        help="Resuelve un problema PDDL del Senku (beam search por defecto).",
    )
    p_resolver.add_argument("--dominio", required=True)
    p_resolver.add_argument("--problema", required=True)
    p_resolver.add_argument(
        "--algoritmo", choices=["beam", "beam-iter", "bfs", "fd"], default="beam",
        help="beam=beam search (junio); beam-iter=beam con beta creciente; "
             "bfs=parte comun; fd=Fast Downward.",
    )
    p_resolver.add_argument("--beta", type=int, default=100,
                            help="Anchura del haz para beam search.")
    p_resolver.add_argument("--intentos", type=int, default=3,
                            help="Numero de reinicios estocasticos.")
    p_resolver.add_argument(
        "--heuristica", choices=["conectividad", "pagoda"], default="conectividad",
        help="Heuristica de beam search: conectividad (recomendada) o pagoda.",
    )
    p_resolver.add_argument(
        "--pagoda", choices=["clasica", "uniforme"], default="clasica",
        help="Asignacion de pesos pagoda (solo si --heuristica pagoda).",
    )
    p_resolver.add_argument("--limite", type=int, default=None,
                            help="Limite de nodos / iteraciones.")
    p_resolver.add_argument("--relajado", action="store_true",
                            help="Modo relajado: meta = una sola pieza en cualquier sitio.")
    p_resolver.add_argument("--sin-visitados", action="store_true",
                            help="Desactiva la memoria de estados visitados (beam search).")
    p_resolver.add_argument("--backend", choices=["auto", "unified_planning", "ligero"],
                            default="auto", help="Parser PDDL a utilizar.")
    p_resolver.add_argument("--fd-search", default=None,
                            help="Configuracion de busqueda de Fast Downward, p.ej. 'astar(hmax())'.")
    p_resolver.set_defaults(func=comando_resolver)

    p_generar = subparsers.add_parser(
        "generar",
        help="Genera los ficheros PDDL de problemas para las cinco variantes.",
    )
    p_generar.add_argument(
        "--destino",
        default="senku/pddl/problemas",
        help="Directorio donde se escriben los ficheros .pddl generados.",
    )
    p_generar.set_defaults(func=comando_generar)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
