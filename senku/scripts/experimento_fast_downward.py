"""Resuelve cada variante del Senku con Fast Downward via unified-planning.

Se utiliza un proceso hijo por variante con timeout para evitar que la
ejecucion completa se bloquee si una variante concreta es muy costosa.

Los resultados se imprimen por consola y se guardan en
`senku/resultados/fast_downward.csv`.
"""

from concurrent.futures import ProcessPoolExecutor, TimeoutError as PFTimeout
from pathlib import Path
import csv
import sys
import time


def _resuelve(variante: int):
    """Funcion ejecutada en un proceso aparte: carga el PDDL y lanza FD."""
    from unified_planning.io import PDDLReader
    from unified_planning.shortcuts import OneshotPlanner, get_environment
    get_environment().credits_stream = None

    raiz = Path(__file__).resolve().parents[2]
    dom = raiz / "senku" / "pddl" / "dominio_senku.pddl"
    prob = raiz / "senku" / "pddl" / "problemas" / f"variante_{variante}.pddl"

    lector = PDDLReader()
    problema = lector.parse_problem(str(dom), str(prob))
    planificador = OneshotPlanner(name="fast-downward")
    inicio = time.perf_counter()
    resultado = planificador.solve(problema)
    tiempo = time.perf_counter() - inicio
    movs = len(resultado.plan.actions) if resultado.plan is not None else 0
    estado = str(resultado.status).split(".")[-1]
    return {
        "variante": variante,
        "estado": estado,
        "movimientos": movs,
        "tiempo_s": round(tiempo, 2),
    }


def main(timeout_s: float = 120.0):
    filas = []
    print(f"Ejecutando Fast Downward (timeout={timeout_s}s por variante)\n")
    for v in [1, 2, 3, 4, 5]:
        with ProcessPoolExecutor(max_workers=1) as exe:
            futuro = exe.submit(_resuelve, v)
            try:
                r = futuro.result(timeout=timeout_s)
            except PFTimeout:
                r = {
                    "variante": v,
                    "estado": "TIMEOUT",
                    "movimientos": 0,
                    "tiempo_s": timeout_s,
                }
                # Cancelacion limpia del proceso hijo
                for proc in exe._processes.values():
                    proc.terminate()
        print(
            f"Variante {v}: estado={r['estado']:30s} "
            f"movs={r['movimientos']:3d} tiempo={r['tiempo_s']:.2f}s"
        )
        filas.append(r)

    destino = Path(__file__).resolve().parents[1] / "resultados" / "fast_downward.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader()
        w.writerows(filas)
    print(f"\nCSV escrito en {destino}")


if __name__ == "__main__":
    timeout = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    main(timeout)
