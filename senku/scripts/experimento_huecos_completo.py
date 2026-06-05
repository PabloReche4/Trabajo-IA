"""Barrido exhaustivo de la posicion del hueco inicial.

Para cada variante, prueba TODAS las casillas como hueco inicial y
comprueba (con beam search iterativo + heuristica de conectividad,
modo relajado) si la instancia es resoluble. Para los tableros con
simetrias, basta con un cuadrante representativo: aqui se aprovechan
las simetrias verticales y horizontales para reducir el numero de
huecos probados.

Genera dos ficheros:
  - resultados/huecos_completo.csv: una fila por cada hueco probado
    (variante, hueco, exito, movs, min_piezas, nodos, tiempo).
  - resultados/huecos_resumen.csv: una fila por variante con el
    porcentaje de huecos resolubles y el numero total.

Diseñado para ejecutarse de una vez:
    python senku/scripts/experimento_huecos_completo.py
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
from senku.src.busqueda import beam_search_iterativo  # noqa: E402


def _representantes_por_simetria(casillas):
    """Devuelve los huecos representativos por simetria del tablero.

    Aprovecha la simetria respecto a los ejes horizontal y vertical:
    si el tablero es simetrico, basta con probar el cuadrante superior
    izquierdo. La mayoria de variantes del Senku son simetricas."""
    filas = [r for r, _ in casillas]
    cols = [c for _, c in casillas]
    r_med = (min(filas) + max(filas)) / 2
    c_med = (min(cols) + max(cols)) / 2
    # Tomamos solo los huecos con r <= r_med y c <= c_med (cuadrante)
    cuadrante = sorted({(r, c) for (r, c) in casillas
                        if r <= r_med + 0.001 and c <= c_med + 0.001})
    return cuadrante


def experimento(timeout_por_hueco: float = 60.0):
    print("== Barrido de huecos iniciales (beam iterativo + conectividad, relajado) ==\n")
    filas_detalle = []
    filas_resumen = []
    for var in [1, 2, 3, 4, 5]:
        base = TABLEROS[var]
        candidatos = _representantes_por_simetria(base.casillas)
        print(f"\n--- Variante {var} ({len(base.casillas)} casillas, "
              f"{len(candidatos)} huecos representativos por simetria) ---")
        exitosos = 0
        min_global = len(base.casillas)
        for hueco in candidatos:
            tablero = _tablero(
                f"var{var}_hueco_{hueco[0]}_{hueco[1]}",
                set(base.casillas), hueco=hueco, objetivo=hueco,
            )
            p = ProblemaSenku.desde_tablero(tablero, modo_relajado=True)
            h = heuristica_conectividad(p)
            inicio = time.perf_counter()
            r = beam_search_iterativo(
                p, h,
                betas=[100, 300, 800],
                intentos_por_beta=3,
                iteraciones_maximas=120,
            )
            t_total = time.perf_counter() - inicio
            if t_total > timeout_por_hueco and not r.exito:
                # No abortamos a mitad pero anotamos como agotado
                pass
            if r.min_piezas_alcanzadas is not None:
                min_global = min(min_global, r.min_piezas_alcanzadas)
            if r.exito:
                exitosos += 1
            filas_detalle.append({
                "variante": var,
                "hueco_fila": hueco[0], "hueco_col": hueco[1],
                "exito": r.exito,
                "movimientos": len(r.movimientos) if r.exito else 0,
                "min_piezas": r.min_piezas_alcanzadas if r.min_piezas_alcanzadas is not None else "",
                "nodos": r.nodos_expandidos,
                "tiempo_s": round(t_total, 1),
            })
            marca = "EXITO" if r.exito else f"min={r.min_piezas_alcanzadas}"
            print(f"  hueco {hueco}: {marca:14s} nodos={r.nodos_expandidos:>7d} t={t_total:.1f}s")
        pct = 100.0 * exitosos / max(1, len(candidatos))
        filas_resumen.append({
            "variante": var,
            "casillas": len(base.casillas),
            "huecos_probados": len(candidatos),
            "huecos_resolubles": exitosos,
            "porcentaje_resolubles": round(pct, 1),
            "min_piezas_absoluto": min_global,
        })
        print(f"  -> {exitosos}/{len(candidatos)} huecos resolubles "
              f"({pct:.1f}%). Min piezas alcanzado: {min_global}")

    destino_det = RAIZ / "senku" / "resultados" / "huecos_completo.csv"
    destino_res = RAIZ / "senku" / "resultados" / "huecos_resumen.csv"
    destino_det.parent.mkdir(parents=True, exist_ok=True)
    with destino_det.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas_detalle[0].keys())
        w.writeheader(); w.writerows(filas_detalle)
    with destino_res.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas_resumen[0].keys())
        w.writeheader(); w.writerows(filas_resumen)
    print(f"\nDetalle: {destino_det}")
    print(f"Resumen: {destino_res}")


if __name__ == "__main__":
    experimento()
