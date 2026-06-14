"""Resolucion con planificadores externos a traves de unified-planning.

`resuelve_con_fast_downward` recibe un Problem de unified-planning y
devuelve el plan que encuentra Fast Downward (si lo hay). Es nuestra
linea de base contra la que comparar el beam search.

Sigue el patron de la Practica 4:

    from unified_planning.shortcuts import OneshotPlanner
    planificador = OneshotPlanner(name='fast-downward')
    resultado = planificador.solve(problema)

El Problem que produce dominio_up.py es STRIPS con tipos, asi que es
compatible con Fast Downward sin mas (como se vio en la Practica 4).
"""

from dataclasses import dataclass, field
import time
from typing import List, Optional, Tuple

from unified_planning.shortcuts import OneshotPlanner, get_environment

from .parche_fd import aplicar_parche

# Aplicamos el parche del UnicodeDecodeError de up-fast-downward 0.5.2
# (lo necesitamos en Windows; en Linux no hace dano).
aplicar_parche()

# Silenciamos los creditos que imprime la biblioteca al construir un
# planificador. Es lo que se sugiere en la Practica 4.
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
    """Lanza Fast Downward sobre el Problem via unified-planning.

    problema_up: instancia de unified_planning.model.Problem.
    busqueda: configuracion de busqueda como cadena. Si es None se usa
        la busqueda por defecto del planificador (en la version actual
        de FD, lazy-greedy con FF). Ejemplos: 'astar(hmax())',
        'astar(add())'.
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
