"""Algoritmos de busqueda sobre el espacio de estados del Senku.

Incluye:
    - busqueda_primero_anchura: BFS basico (parte comun del trabajo)
    - busqueda_primero_profundidad: DFS con limite, util como referencia
    - beam_search: algoritmo especifico de la convocatoria de junio
    - beam_search_estocastico: variante con reinicio aleatorio y desempate

Todos devuelven un objeto Resultado homogeneo con la informacion del
camino encontrado (si existe) y estadisticas de la ejecucion.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set
import random
import time
from collections import deque

from .estado import Estado, Movimiento, ProblemaSenku, reconstruye_camino


@dataclass
class Resultado:
    """Resultado de una busqueda en el espacio de estados."""

    exito: bool
    movimientos: List[Movimiento] = field(default_factory=list)
    estados: List[Estado] = field(default_factory=list)
    nodos_expandidos: int = 0
    tiempo_segundos: float = 0.0
    parametros: dict = field(default_factory=dict)

    def __str__(self) -> str:
        cabecera = "Solucion encontrada" if self.exito else "Sin solucion"
        return (
            f"{cabecera} | movimientos={len(self.movimientos)} "
            f"| nodos={self.nodos_expandidos} | tiempo={self.tiempo_segundos:.3f}s "
            f"| params={self.parametros}"
        )


def busqueda_primero_anchura(
    problema: ProblemaSenku, limite_nodos: Optional[int] = None
) -> Resultado:
    """BFS clasica para encontrar una solucion con el minimo numero de
    movimientos. El parametro `limite_nodos` permite acotar el numero de
    estados explorados (necesario en tableros grandes; el Senku tiene un
    espacio de estados exponencial)."""
    inicio = time.perf_counter()
    if problema.es_meta(problema.inicial):
        return Resultado(
            exito=True,
            estados=[problema.inicial],
            tiempo_segundos=time.perf_counter() - inicio,
            parametros={"algoritmo": "BFS"},
        )

    visitados: Set[Estado] = {problema.inicial}
    padres = {problema.inicial: None}
    cola = deque([problema.inicial])
    expandidos = 0

    while cola:
        estado = cola.popleft()
        expandidos += 1
        if limite_nodos is not None and expandidos > limite_nodos:
            break
        for movimiento, sucesor in problema.sucesores(estado):
            if sucesor in visitados:
                continue
            visitados.add(sucesor)
            padres[sucesor] = (movimiento, estado)
            if problema.es_meta(sucesor):
                estados, movimientos = reconstruye_camino(padres, sucesor)
                return Resultado(
                    exito=True,
                    estados=estados,
                    movimientos=movimientos,
                    nodos_expandidos=expandidos,
                    tiempo_segundos=time.perf_counter() - inicio,
                    parametros={"algoritmo": "BFS"},
                )
            cola.append(sucesor)
    return Resultado(
        exito=False,
        nodos_expandidos=expandidos,
        tiempo_segundos=time.perf_counter() - inicio,
        parametros={"algoritmo": "BFS", "limite_nodos": limite_nodos},
    )


def busqueda_primero_profundidad(
    problema: ProblemaSenku, limite_profundidad: Optional[int] = None
) -> Resultado:
    """DFS iterativa con control de profundidad. Se incluye como
    referencia para comparar contra el beam search."""
    inicio = time.perf_counter()
    pila = [(problema.inicial, [], [problema.inicial])]
    expandidos = 0

    while pila:
        estado, movimientos, camino = pila.pop()
        expandidos += 1
        if problema.es_meta(estado):
            return Resultado(
                exito=True,
                estados=camino,
                movimientos=movimientos,
                nodos_expandidos=expandidos,
                tiempo_segundos=time.perf_counter() - inicio,
                parametros={"algoritmo": "DFS"},
            )
        if limite_profundidad is not None and len(movimientos) >= limite_profundidad:
            continue
        for movimiento, sucesor in problema.sucesores(estado):
            if sucesor in camino:
                continue
            pila.append((sucesor, movimientos + [movimiento], camino + [sucesor]))
    return Resultado(
        exito=False,
        nodos_expandidos=expandidos,
        tiempo_segundos=time.perf_counter() - inicio,
        parametros={"algoritmo": "DFS", "limite_profundidad": limite_profundidad},
    )


def beam_search(
    problema: ProblemaSenku,
    heuristica: Callable[[Estado], float],
    beta: int = 10,
    iteraciones_maximas: Optional[int] = None,
    usar_visitados: bool = True,
    semilla: Optional[int] = None,
) -> Resultado:
    """Beam Search siguiendo la definicion del enunciado.

    Pasos del algoritmo:
        1. Se prefija una anchura del rayo `beta`.
        2. Se parte de una frontera formada solo por el estado inicial.
        3. Para cada estado de la frontera se generan todos sus sucesores.
        4. Si alguno de los sucesores es meta, se devuelve la secuencia
           de movimientos.
        5. En caso contrario, se ordenan los sucesores segun la
           heuristica y se conservan los `beta` mejores como nueva
           frontera. Se repite el proceso.

    Parametros adicionales:
        usar_visitados: si es True, se mantiene una memoria global de
            estados ya considerados para evitar exploracion redundante;
            si es False se permite revisitar estados (variante de la
            literatura util cuando la heuristica tiende a llevar la
            busqueda a callejones sin salida).
        semilla: semilla del generador aleatorio usado como criterio de
            desempate. Permite reproducir experimentos y diversificar
            ejecuciones sucesivas.
    """
    inicio = time.perf_counter()
    rng = random.Random(semilla)
    if problema.es_meta(problema.inicial):
        return Resultado(
            exito=True,
            estados=[problema.inicial],
            tiempo_segundos=time.perf_counter() - inicio,
            parametros={"algoritmo": "BeamSearch", "beta": beta},
        )

    padres = {problema.inicial: None}
    visitados: Set[Estado] = {problema.inicial} if usar_visitados else set()
    frontera: List[Estado] = [problema.inicial]
    expandidos = 0
    iteraciones = 0

    while frontera:
        iteraciones += 1
        if iteraciones_maximas is not None and iteraciones > iteraciones_maximas:
            break
        candidatos = []
        for estado in frontera:
            expandidos += 1
            for movimiento, sucesor in problema.sucesores(estado):
                if usar_visitados and sucesor in visitados:
                    continue
                # Solo registramos padre la primera vez que vemos el estado
                if sucesor not in padres:
                    padres[sucesor] = (movimiento, estado)
                if problema.es_meta(sucesor):
                    estados, movimientos = reconstruye_camino(padres, sucesor)
                    return Resultado(
                        exito=True,
                        estados=estados,
                        movimientos=movimientos,
                        nodos_expandidos=expandidos,
                        tiempo_segundos=time.perf_counter() - inicio,
                        parametros={
                            "algoritmo": "BeamSearch",
                            "beta": beta,
                            "iteraciones": iteraciones,
                            "usar_visitados": usar_visitados,
                        },
                    )
                if usar_visitados:
                    visitados.add(sucesor)
                candidatos.append((heuristica(sucesor), sucesor))
        candidatos = [c for c in candidatos if c[0] != float("inf")]
        # Desempate aleatorio: anadimos un valor pseudoaleatorio como
        # segundo criterio de orden. Esto evita que el beam quede
        # determinista cuando varios sucesores comparten heuristica.
        candidatos.sort(key=lambda x: (x[0], rng.random()))
        frontera = [estado for _, estado in candidatos[:beta]]

    return Resultado(
        exito=False,
        nodos_expandidos=expandidos,
        tiempo_segundos=time.perf_counter() - inicio,
        parametros={
            "algoritmo": "BeamSearch",
            "beta": beta,
            "iteraciones": iteraciones,
            "usar_visitados": usar_visitados,
        },
    )


def beam_search_con_reinicios(
    problema: ProblemaSenku,
    heuristica: Callable[[Estado], float],
    beta: int = 10,
    intentos: int = 5,
    iteraciones_maximas: Optional[int] = None,
    usar_visitados: bool = True,
) -> Resultado:
    """Repite beam_search con distintas semillas y devuelve el primer
    resultado exitoso (o el ultimo fallido).

    Beam search es un algoritmo incompleto: la combinacion de heuristica
    y desempate determinista puede empujar la busqueda a callejones sin
    salida especificos. Ejecutar varios intentos con desempate aleatorio
    incrementa significativamente la probabilidad de exito en problemas
    como el Senku, en el que las soluciones son escasas."""
    mejor_fallo = None
    inicio_total = time.perf_counter()
    nodos_totales = 0
    for intento in range(intentos):
        r = beam_search(
            problema=problema,
            heuristica=heuristica,
            beta=beta,
            iteraciones_maximas=iteraciones_maximas,
            usar_visitados=usar_visitados,
            semilla=intento,
        )
        nodos_totales += r.nodos_expandidos
        if r.exito:
            r.tiempo_segundos = time.perf_counter() - inicio_total
            r.nodos_expandidos = nodos_totales
            r.parametros["intento_exitoso"] = intento
            r.parametros["intentos_totales"] = intento + 1
            return r
        mejor_fallo = r
    if mejor_fallo is not None:
        mejor_fallo.tiempo_segundos = time.perf_counter() - inicio_total
        mejor_fallo.nodos_expandidos = nodos_totales
        mejor_fallo.parametros["intentos_totales"] = intentos
    return mejor_fallo  # type: ignore[return-value]
