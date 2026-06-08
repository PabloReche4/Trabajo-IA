"""Prueba Fast Downward sobre V1 y V5 con huecos iniciales alternativos.

Beam search ha demostrado que las variantes 1 (octogono) y 5 (rombo)
con sus huecos iniciales nominales son dificiles para FD.

Probamos aqui huecos alternativos que el barrido empirico ha clasificado como
resolubles, con la esperanza de que esos sean mas faciles para FD
tambien.
"""

from concurrent.futures import ProcessPoolExecutor, TimeoutError as PFTimeout
from pathlib import Path
import csv
import sys
import time


def _fd(args):
    variante, ruta_problema = args
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
        str(raiz / "senku/pddl/problemas" / ruta_problema),
    )
    inicio = time.perf_counter()
    try:
        r = OneshotPlanner(name="fast-downward").solve(p)
        return {
            "variante": variante,
            "problema": ruta_problema,
            "estado": str(r.status).split(".")[-1],
            "movs": len(r.plan.actions) if r.plan else 0,
            "tiempo_s": round(time.perf_counter() - inicio, 2),
        }
    except Exception as e:
        return {
            "variante": variante,
            "problema": ruta_problema,
            "estado": f"ERROR:{type(e).__name__}",
            "movs": 0,
            "tiempo_s": round(time.perf_counter() - inicio, 2),
        }


def main(timeout_s: float = 120.0):
    # Lista de (variante, fichero) a probar
    candidatos = [
        (1, "variante_1.pddl"),                # Octogono con hueco nominal
        (1, "variante_1_hueco_0_2.pddl"),      # Octogono con hueco (0,2)
        (5, "variante_5.pddl"),                # Rombo con hueco nominal
        (5, "variante_5_hueco_4_2.pddl"),      # Rombo con hueco (4,2)
    ]
    print(f"Probando huecos alternativos para V1 y V5 (timeout {timeout_s}s c/u)\n")
    filas = []
    for var, problema in candidatos:
        with ProcessPoolExecutor(max_workers=1) as exe:
            fut = exe.submit(_fd, (var, problema))
            try:
                r = fut.result(timeout=timeout_s)
            except PFTimeout:
                r = {"variante": var, "problema": problema,
                     "estado": "TIMEOUT", "movs": 0,
                     "tiempo_s": timeout_s}
                for proc in exe._processes.values():
                    proc.terminate()
        marca = "SOLVED" if r["estado"].startswith("SOLVED") else r["estado"]
        print(f"V{var} {problema:38s}: {marca:30s} movs={r['movs']:3d} t={r['tiempo_s']:.1f}s")
        filas.append(r)
    destino = (Path(__file__).resolve().parents[1]
               / "resultados" / "fd_huecos_alternativos.csv")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader(); w.writerows(filas)
    print(f"\nCSV: {destino}")


if __name__ == "__main__":
    t = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    main(t)
