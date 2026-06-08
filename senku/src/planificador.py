"""Wrapper sobre Fast Downward via unified-planning."""

from dataclasses import dataclass, field
import time
from typing import List, Optional, Tuple

from unified_planning.shortcuts import OneshotPlanner, get_environment

from .parche_fd import aplicar_parche

# Parche del UnicodeDecodeError de up-fast-downward 0.5.2 en Windows.
aplicar_parche()
get_environment().credits_stream = None


@dataclass
class ResultadoPlanificador:
    exito: bool
    estado: str
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
