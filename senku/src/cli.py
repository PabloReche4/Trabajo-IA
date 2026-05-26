"""Interfaz de linea de comandos para resolver problemas de Senku.

Uso tipico (desde la raiz del proyecto):

    python -m senku.src.cli resolver \\
        --dominio senku/pddl/dominio_senku.pddl \\
        --problema senku/pddl/problemas/variante_1.pddl \\
        --beta 100 --intentos 3

El comando `resolver` ejecuta beam search sobre el par de ficheros PDDL
proporcionado y devuelve la secuencia de movimientos que conducen al
estado meta (si la encuentra). El parametro `--beta` controla la anchura
del haz; `--intentos` permite ejecutar varias replicas con desempate
aleatorio para mitigar la incompletud del algoritmo.

Adicionalmente se proporciona el comando `generar` para producir los
ficheros .pddl de problemas a partir de las variantes definidas en el
modulo `tableros`.
"""

import argparse
import sys
from pathlib import Path

from .busqueda import beam_search_con_reinicios, busqueda_primero_anchura
from .generador_pddl import escribe_problema
from .heuristicas import (
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
        problema = problema.__class__(
            tablero=problema.tablero,
            inicial=problema.inicial,
            meta_ocupadas=problema.meta_ocupadas,
            meta_vacias=problema.meta_vacias,
            saltos=problema.saltos,
            modo_relajado=True,
        )

    pesos = pagoda_clasica(problema.tablero) if args.pagoda == "clasica" else pagoda_uniforme(problema.tablero)
    h = heuristica_pagoda(problema, pesos)

    if args.algoritmo == "bfs":
        resultado = busqueda_primero_anchura(problema, limite_nodos=args.limite)
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
        "--algoritmo", choices=["beam", "bfs"], default="beam",
        help="Algoritmo a ejecutar.",
    )
    p_resolver.add_argument("--beta", type=int, default=100,
                            help="Anchura del haz para beam search.")
    p_resolver.add_argument("--intentos", type=int, default=3,
                            help="Numero de reinicios estocasticos.")
    p_resolver.add_argument(
        "--pagoda", choices=["clasica", "uniforme"], default="clasica",
        help="Asignacion de pesos pagoda a utilizar.",
    )
    p_resolver.add_argument("--limite", type=int, default=None,
                            help="Limite de nodos / iteraciones.")
    p_resolver.add_argument("--relajado", action="store_true",
                            help="Modo relajado: meta = una sola pieza en cualquier sitio.")
    p_resolver.add_argument("--sin-visitados", action="store_true",
                            help="Desactiva la memoria de estados visitados.")
    p_resolver.add_argument("--backend", choices=["auto", "unified_planning", "ligero"],
                            default="auto", help="Parser PDDL a utilizar.")
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
