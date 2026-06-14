"""Lanza Fast Downward sobre una sola variante (con timeout por subproceso).

Util para investigar variantes que crashean en el script global.
"""
from concurrent.futures import ProcessPoolExecutor, TimeoutError as PFTimeout
from pathlib import Path
import csv
import sys
import time


def _fd(variante: int):
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
        str(raiz/"senku/pddl/dominio_senku.pddl"),
        str(raiz/f"senku/pddl/problemas/variante_{variante}.pddl"))
    inicio = time.perf_counter()
    try:
        r = OneshotPlanner(name="fast-downward").solve(p)
        return {
            "variante": variante,
            "estado": str(r.status).split(".")[-1],
            "movs": len(r.plan.actions) if r.plan else 0,
            "tiempo_s": round(time.perf_counter() - inicio, 2),
        }
    except Exception as e:
        return {
            "variante": variante,
            "estado": f"ERROR: {type(e).__name__}",
            "movs": 0,
            "tiempo_s": round(time.perf_counter() - inicio, 2),
        }


def main(timeout_s: float = 180.0, variantes=None):
    variantes = variantes or [1, 2, 3, 4, 5]
    filas = []
    for v in variantes:
        with ProcessPoolExecutor(max_workers=1) as exe:
            futuro = exe.submit(_fd, v)
            try:
                r = futuro.result(timeout=timeout_s)
            except PFTimeout:
                r = {"variante": v, "estado": "TIMEOUT", "movs": 0, "tiempo_s": timeout_s}
                for proc in exe._processes.values():
                    proc.terminate()
            except Exception as e:
                r = {"variante": v, "estado": f"ERROR: {type(e).__name__}: {e}",
                     "movs": 0, "tiempo_s": timeout_s}
        print(f"V{v}: estado={r['estado']:35s} movs={r['movs']:3d} tiempo={r['tiempo_s']:.1f}s")
        filas.append(r)
    destino = Path(__file__).resolve().parents[1] / "resultados" / "fast_downward.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader(); w.writerows(filas)
    print(f"CSV: {destino}")


if __name__ == "__main__":
    timeout = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
    variantes = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else None
    main(timeout, variantes)
