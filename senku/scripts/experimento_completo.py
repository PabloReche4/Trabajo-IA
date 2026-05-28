"""Experimento completo de beam search con la heuristica de conectividad.

Genera dos CSV:
  - resultados/beam_conectividad.csv: para cada variante, intenta beam
    search en modo relajado (1 pieza en cualquier sitio) y, si procede,
    en modo estricto (1 pieza en el centro), con anchura creciente.
  - resultados/estudio_huecos.csv: sobre la cruz inglesa, prueba
    distintas posiciones del hueco inicial y comprueba en cuales beam
    search consigue terminar con una unica pieza en ese mismo hueco
    (problema complementario).

Diseñado para ejecutarse de una vez:
    python senku/scripts/experimento_completo.py
"""

from pathlib import Path
import csv
import sys
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from senku.src.tableros import TABLEROS, _tablero  # noqa: E402
from senku.src.estado import ProblemaSenku  # noqa: E402
from senku.src.heuristicas import heuristica_conectividad  # noqa: E402
from senku.src.busqueda import beam_search_con_reinicios  # noqa: E402


def experimento_variantes():
    print("== Beam search + conectividad sobre las 5 variantes ==\n")
    filas = []
    # Anchuras crecientes segun tamano del tablero
    config = {
        1: (300, 6), 2: (800, 6), 3: (1500, 6),
        4: (800, 6), 5: (2000, 6),
    }
    for var in [1, 2, 3, 4, 5]:
        t = TABLEROS[var]
        beta, intentos = config[var]
        for modo in [True, False]:  # relajado primero
            p = ProblemaSenku.desde_tablero(t, modo_relajado=modo)
            h = heuristica_conectividad(p)
            r = beam_search_con_reinicios(
                p, h, beta=beta, intentos=intentos, iteraciones_maximas=120
            )
            fila = {
                "variante": var, "casillas": len(t.casillas),
                "modo": "relajado" if modo else "estricto",
                "beta": beta, "intentos": intentos,
                "exito": r.exito, "movimientos": len(r.movimientos),
                "nodos": r.nodos_expandidos, "tiempo_s": round(r.tiempo_segundos, 1),
            }
            filas.append(fila)
            print(f"V{var} ({len(t.casillas)} cas) {fila['modo']:9s} "
                  f"beta={beta}: "
                  f"{'EXITO ' + str(len(r.movimientos)) + 'mov' if r.exito else 'sin sol':14s} "
                  f"nodos={r.nodos_expandidos} t={fila['tiempo_s']}s")
    destino = RAIZ / "senku" / "resultados" / "beam_conectividad.csv"
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader(); w.writerows(filas)
    print(f"\nCSV: {destino}\n")


def experimento_huecos():
    print("== Estudio de la posicion del hueco inicial (cruz inglesa) ==")
    print("   (beam search, modo estricto: terminar en el propio hueco)\n")
    base = TABLEROS[1]
    # Por simetria de la cruz inglesa, basta un cuadrante representativo.
    candidatas = sorted({c for c in base.casillas if c[0] <= 3 and c[1] <= 3})
    filas = []
    for hueco in candidatas:
        tablero = _tablero(
            f"cruz_hueco_{hueco[0]}_{hueco[1]}",
            set(base.casillas), hueco=hueco, objetivo=hueco,
        )
        p = ProblemaSenku.desde_tablero(tablero, modo_relajado=False)
        h = heuristica_conectividad(p)
        r = beam_search_con_reinicios(
            p, h, beta=500, intentos=8, iteraciones_maximas=120
        )
        fila = {
            "hueco_fila": hueco[0], "hueco_col": hueco[1],
            "exito": r.exito, "movimientos": len(r.movimientos),
            "nodos": r.nodos_expandidos, "tiempo_s": round(r.tiempo_segundos, 1),
        }
        filas.append(fila)
        print(f"Hueco {hueco}: "
              f"{'COMPLEMENTARIO OK ' + str(len(r.movimientos)) + 'mov' if r.exito else 'no encontrado':22s} "
              f"nodos={r.nodos_expandidos} t={fila['tiempo_s']}s")
    destino = RAIZ / "senku" / "resultados" / "estudio_huecos.csv"
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader(); w.writerows(filas)
    print(f"\nCSV: {destino}")


if __name__ == "__main__":
    experimento_variantes()
    experimento_huecos()
