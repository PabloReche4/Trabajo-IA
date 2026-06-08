"""
Estudio de distintas posiciones iniciales del hueco en la cruz inglesa.

Este programa genera automáticamente varios problemas de peg solitaire
sobre el tablero de la cruz inglesa. Para cada casilla candidata se crea
una configuración inicial en la que dicha casilla está vacía y se define
como objetivo terminar la partida con una única ficha situada exactamente
en esa misma posición.

Cada instancia se modela mediante Unified Planning y se resuelve con el
planificador Fast Downward. La ejecución de cada problema se realiza en
un subproceso independiente con un tiempo máximo de ejecución para evitar
bloqueos prolongados.

Los resultados obtenidos para cada posición incluyen el estado de la
búsqueda, el número de movimientos del plan encontrado y el tiempo de
resolución. Finalmente, toda la información se almacena en el archivo:

senku/resultados/estudio_huecos.csv
"""

from concurrent.futures import ProcessPoolExecutor, TimeoutError as PFTimeout
from pathlib import Path
import csv
import sys
import time


def _resuelve_hueco(args):
    """Construye el problema (hueco en h, meta en h) y lo resuelve con FD."""
    fila, col = args
    from unified_planning.shortcuts import OneshotPlanner, get_environment
    get_environment().credits_stream = None

    # Importacion del paquete del proyecto
    raiz = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(raiz))
    from senku.src.tableros import _tablero, TABLEROS  # noqa
    from senku.src.dominio_up import construye_problema_up

    base = TABLEROS[1]  # cruz inglesa
    hueco = (fila, col)
    tablero = _tablero(
        f"cruz_hueco_{fila}_{col}", set(base.casillas), hueco=hueco, objetivo=hueco
    )
    problema = construye_problema_up(tablero)
    inicio = time.perf_counter()
    try:
        r = OneshotPlanner(name="fast-downward").solve(problema)
        return {
            "fila": fila, "col": col,
            "estado": str(r.status).split(".")[-1],
            "movs": len(r.plan.actions) if r.plan else 0,
            "tiempo_s": round(time.perf_counter() - inicio, 1),
        }
    except Exception as e:
        return {
            "fila": fila, "col": col,
            "estado": f"ERROR:{type(e).__name__}",
            "movs": 0, "tiempo_s": round(time.perf_counter() - inicio, 1),
        }


def main(timeout_s: float = 60.0):
    raiz = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(raiz))
    from senku.src.tableros import TABLEROS

    base = TABLEROS[1]
    # Por simetria de la cruz inglesa basta el sector superior-izquierdo,
    # pero recorremos un subconjunto representativo de posiciones distintas.
    candidatas = sorted({
        c for c in base.casillas
        if c[0] <= 3 and c[1] <= 3  # cuadrante representativo
    })
    print(f"Estudio de {len(candidatas)} posiciones del hueco "
          f"(timeout {timeout_s}s c/u)\n")

    filas = []
    for h in candidatas:
        with ProcessPoolExecutor(max_workers=1) as exe:
            fut = exe.submit(_resuelve_hueco, h)
            try:
                r = fut.result(timeout=timeout_s)
            except PFTimeout:
                r = {"fila": h[0], "col": h[1], "estado": "TIMEOUT",
                     "movs": 0, "tiempo_s": timeout_s}
                for proc in exe._processes.values():
                    proc.terminate()
        marca = "RESUELTO" if r["estado"].startswith("SOLVED") else r["estado"]
        print(f"Hueco {h}: {marca:30s} movs={r['movs']:3d} t={r['tiempo_s']}s")
        filas.append(r)

    destino = raiz / "senku" / "resultados" / "estudio_huecos.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader(); w.writerows(filas)
    print(f"\nCSV: {destino}")


if __name__ == "__main__":
    t = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    main(t)
