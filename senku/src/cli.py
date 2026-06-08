"""CLI para resolver problemas de Senku."""

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
    )
    p_resolver.add_argument("--beta", type=int, default=100)
    p_resolver.add_argument("--intentos", type=int, default=3)
    p_resolver.add_argument(
        "--heuristica", choices=["conectividad", "pagoda"], default="conectividad",
    )
    p_resolver.add_argument(
        "--pagoda", choices=["clasica", "uniforme"], default="clasica",
    )
    p_resolver.add_argument("--limite", type=int, default=None)
    p_resolver.add_argument("--relajado", action="store_true")
    p_resolver.add_argument("--sin-visitados", action="store_true")
    p_resolver.add_argument(
        "--backend", choices=["auto", "unified_planning", "ligero"], default="auto",
    )
    p_resolver.add_argument("--fd-search", default=None)
    p_resolver.set_defaults(func=comando_resolver)

    p_generar = subparsers.add_parser(
        "generar",
        help="Genera los ficheros PDDL de problemas para las cinco variantes.",
    )
    p_generar.add_argument(
        "--destino",
        default="senku/pddl/problemas",
    )
    p_generar.set_defaults(func=comando_generar)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
