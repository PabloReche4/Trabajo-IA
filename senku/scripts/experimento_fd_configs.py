"""Prueba distintas configuraciones de busqueda de Fast Downward sobre
las variantes obligatorias (V1, V3, V5).

Fast Downward acepta cadenas que describen la combinacion (algoritmo,
heuristica) a usar. Algunas configuraciones tipicas:

  lazy_greedy([ff()])   - lazy greedy con FF (defecto satisficing)
  eager_greedy([ff()])  - eager greedy con FF
  astar(ff())           - A* con FF
  astar(add())          - A* con h^add
  astar(hmax())         - A* con h^max (admisible, lento)
  lazy(alt([single(ff())]))  - lazy con FF en alternancia

Se ejecuta cada variante con varias configuraciones y se reporta la
primera que encuentra solucion dentro del timeout.
"""

from concurrent.futures import ProcessPoolExecutor, TimeoutError as PFTimeout
from pathlib import Path
import csv
import sys
import time


def _fd_con_config(args):
    variante, config = args
    import sys as _sys
    from pathlib import Path as _Path
    _raiz = _Path(__file__).resolve().parents[2]
    if str(_raiz) not in _sys.path:
        _sys.path.insert(0, str(_raiz))
    from senku.src.parche_fd import aplicar_parche
    aplicar_parche()
    from unified_planning.io import PDDLReader
    from unified_planning.shortcuts import OneshotPlanner, get_environment
    get_environment().credits_stream = None

    raiz = Path(__file__).resolve().parents[2]
    p = PDDLReader().parse_problem(
        str(raiz / "senku/pddl/dominio_senku.pddl"),
        str(raiz / f"senku/pddl/problemas/variante_{variante}.pddl"),
    )
    inicio = time.perf_counter()
    try:
        params = {"fast_downward_search_config": config} if config else {}
        planner = OneshotPlanner(name="fast-downward", params=params)
        r = planner.solve(p)
        return {
            "variante": variante,
            "config": config or "default",
            "estado": str(r.status).split(".")[-1],
            "movs": len(r.plan.actions) if r.plan else 0,
            "tiempo_s": round(time.perf_counter() - inicio, 2),
        }
    except Exception as e:
        return {
            "variante": variante,
            "config": config or "default",
            "estado": f"ERROR:{type(e).__name__}",
            "movs": 0,
            "tiempo_s": round(time.perf_counter() - inicio, 2),
        }


def main(timeout_s: float = 120.0):
    configs = [
        None,  # default (lazy-greedy con FF)
        "lazy_greedy([ff()])",
        "eager_greedy([ff()])",
        "astar(add())",
        "astar(hmax())",
        "astar(ff())",
    ]
    variantes_obligatorias = [1, 3, 5]
    filas = []
    print(f"Probando configs de Fast Downward (timeout {timeout_s}s c/u)\n")
    for v in variantes_obligatorias:
        print(f"--- Variante {v} ---")
        for config in configs:
            label = config or "default"
            with ProcessPoolExecutor(max_workers=1) as exe:
                fut = exe.submit(_fd_con_config, (v, config))
                try:
                    r = fut.result(timeout=timeout_s)
                except PFTimeout:
                    r = {"variante": v, "config": label,
                         "estado": "TIMEOUT", "movs": 0,
                         "tiempo_s": timeout_s}
                    for proc in exe._processes.values():
                        proc.terminate()
                except Exception as e:
                    r = {"variante": v, "config": label,
                         "estado": f"ERROR:{type(e).__name__}",
                         "movs": 0, "tiempo_s": timeout_s}
            marca = "SOLVED" if r["estado"].startswith("SOLVED") else r["estado"]
            print(f"  config={label:25s}: {marca:30s} movs={r['movs']:3d} t={r['tiempo_s']:.1f}s")
            filas.append(r)
            if r["estado"].startswith("SOLVED"):
                # Encontrada una config exitosa para esta variante, pasamos
                # a la siguiente
                break
        print()
    destino = (Path(__file__).resolve().parents[1]
               / "resultados" / "fast_downward_configs.csv")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader(); w.writerows(filas)
    print(f"CSV: {destino}")


if __name__ == "__main__":
    t = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    main(t)
