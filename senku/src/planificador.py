"""Resolucion mediante planificadores externos via unified-planning.

Este modulo proporciona una funcion `resuelve_con_fast_downward` que
toma un objeto `Problem` de unified-planning y devuelve el plan
encontrado por Fast Downward (si lo hay). Se usa como linea base para
contrastar la calidad de los planes que produce nuestro beam search.

Sigue exactamente el patron mostrado en la Practica 4:

    from unified_planning.shortcuts import OneshotPlanner
    planificador = OneshotPlanner(name='fast-downward')
    resultado = planificador.solve(problema)

El tipo de problema generado por nuestro modulo `dominio_up.py` es
compatible con Fast Downward (planificacion clasica STRIPS con
tipos), tal y como se comprueba en la propia Practica 4.
"""

from dataclasses import dataclass, field
import time
from typing import List, Optional, Tuple

from unified_planning.shortcuts import OneshotPlanner, get_environment

# Por defecto desactivamos la cabecera de creditos que imprime la
# biblioteca cada vez que se construye un planificador; en la Practica 4
# se sugiere expresamente esta linea.
get_environment().credits_stream = None


@dataclass
class ResultadoPlanificador:
    """Resultado de invocar un planificador externo."""

    exito: bool
    estado: str  # status devuelto por unified-planning (cadena legible)
    movimientos: List[str] = field(default_factory=list)
    tiempo_segundos: float = 0.0
    parametros: dict = field(default_factory=dict)

    def __str__(self) -> str:
        prefijo = "Resuelto" if self.exito else "No resuelto"
        return (
            f"{prefijo} ({self.estado}) | movs={len(self.movimientos)} "
            f"| tiempo={self.tiempo_segundos:.2f}s | params={self.parametros}"
        )


def resuelve_con_fast_downward(
    problema_up,
    busqueda: Optional[str] = None,
) -> ResultadoPlanificador:
    """Invoca Fast Downward via unified-planning.

    Parametros:
        problema_up: instancia de `unified_planning.model.Problem`.
        busqueda: cadena con la configuracion de busqueda. Si es None,
            se usa la busqueda por defecto del planificador (que en la
            version actual de Fast Downward es la lazy-greedy con FF).
            Para utilizar A* con la heuristica h^max se pasaria
            'astar(hmax())'; con h^add: 'astar(add())'.
    """
    inicio = time.perf_counter()
    parametros = {}
    if busqueda is not None:
        parametros["fast_downward_search_config"] = busqueda
    planificador = OneshotPlanner(name="fast-downward", params=parametros)
    if not planificador.supports(problema_up.kind):
        raise RuntimeError(
            f"Fast Downward no soporta {problema_up.kind}"
        )
    resultado_up = planificador.solve(problema_up)
    tiempo = time.perf_counter() - inicio

    movimientos: List[str] = []
    exito = resultado_up.plan is not None
    if exito:
        for accion in resultado_up.plan.actions:
            movimientos.append(str(accion))

    return ResultadoPlanificador(
        exito=exito,
        estado=str(resultado_up.status).split(".")[-1],
        movimientos=movimientos,
        tiempo_segundos=tiempo,
        parametros={"engine": "Fast Downward", "search": busqueda or "default"},
    )
